# NOTA: Esto es un archivo con EXACTAMENTE lo mismo que el notebook, solamente queriamos una forma mas rapida de poder probar con otras fotos

import cv2
import numpy as np


def homo(points_2d):
  n = points_2d.shape[0]
  z = np.ones((n, 1))
  return np.hstack((points_2d, z))


def cart(h_points):
  x = h_points[:, 0]
  y = h_points[:, 1]
  z = h_points[:, 2]
  return np.stack((x/z, y/z)).T


def apply_transform(shape, T):
  h_ori = homo(shape)
  h_dst = np.dot(T, h_ori.T)
  dst = cart(h_dst.T)
  return dst


def anms(keypoints, N):
    Kl = len(keypoints)
    SD = 0
    R = np.full(Kl, np.inf)

    for i in range(Kl):
        for j in range(Kl):
            if keypoints[j].response > keypoints[i].response:
                xi, yi = keypoints[i].pt
                xj, yj = keypoints[j].pt
                SD = (xi - xj)**2 + (yi - yj)**2

                if SD < R[i]:
                    R[i] = SD

    best_R_indexes = np.argsort(R)[::-1]
    best_N_indexes = best_R_indexes[:N]

    return best_N_indexes


def match_bf(des_query, des_train, crossCheck):
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=crossCheck)
    return bf.match(des_query, des_train)


def match_lowe(des_query, des_train, ratio):
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
    matches = bf.knnMatch(des_query, des_train, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < ratio * n.distance:
            good_matches.append(m)

    return good_matches


def interseccion(matches_lowe, matches_cc):
    pares_cc = {(m.queryIdx, m.trainIdx) for m in matches_cc}
    return [m for m in matches_lowe if (m.queryIdx, m.trainIdx) in pares_cc]


def dlt(origen, destino):
    A = []
    b = []
    for i in range(4):
        x, y = origen[i]
        x_prima, y_prima = destino[i]
        A.append([-x, -y, -1, 0, 0, 0, x * x_prima, y * x_prima])
        A.append([0, 0, 0, -x, -y, -1, x * y_prima, y * y_prima])
        b.append(x_prima)
        b.append(y_prima)

    A = np.array(A)
    b = np.array(b)

    H = -np.linalg.solve(A, b)

    H = np.hstack([H, [1]])

    H = H.reshape(3, 3)

    return H


def estimar_homografia_svd(ori, dst):
  A = []

  for i in range(len(ori)):
    x, y = ori[i]
    x_prima, y_prima = dst[i]
    A.append([-x, -y, -1, 0, 0, 0, x * x_prima, y * x_prima, x_prima])
    A.append([0, 0, 0, -x, -y, -1, x * y_prima, y * y_prima, y_prima])

  A = np.array(A)

  _, _, Vt = np.linalg.svd(A)

  h = Vt[-1, :]

  H = h.reshape(3, 3)

  return H


def RANSAC(origins, destinations, t, N):
  rng = np.random.default_rng(0)
  best_inliers = np.zeros(len(origins), dtype=bool)
  best_count = 0

  for _ in range(N):
    indexes_sample = rng.choice(len(origins), size=4, replace=False)
    origen_muestra = origins[indexes_sample]
    destino_muestra = destinations[indexes_sample]

    try:
      H = dlt(origen_muestra, destino_muestra)
    except np.linalg.LinAlgError:
      continue

    errors = np.linalg.norm(apply_transform(origins, H) - destinations, axis=1)
    inliers_count = (errors < t).sum()

    if inliers_count > best_count:
      best_count = inliers_count
      best_inliers = errors < t

  best_origins = origins[best_inliers]
  best_destinations = destinations[best_inliers]

  H_final = estimar_homografia_svd(best_origins, best_destinations)

  errors = np.linalg.norm(apply_transform(origins, H_final) - destinations, axis=1)
  best_inliers = errors < t

  best_origins = origins[best_inliers]
  best_destinations = destinations[best_inliers]

  H_final = estimar_homografia_svd(best_origins, best_destinations)
  H_final = H_final / H_final[2, 2]

  return H_final, best_inliers


def features_anms(img, N_ANMS):
    kp, des = cv2.SIFT_create().detectAndCompute(img, None)
    indexes = anms(kp, N_ANMS)
    kp_anms = [kp[i] for i in indexes]
    des_anms = des[indexes]
    return kp_anms, des_anms


def homografia_par(kp_lateral, des_lateral, kp_centro_anms, des_centro_anms, RATIO, T_RANSAC, N_RANSAC):
    matches_cc = match_bf(des_centro_anms, des_lateral, crossCheck=True)
    matches_lowe = match_lowe(des_centro_anms, des_lateral, RATIO)
    matches = interseccion(matches_lowe, matches_cc)

    origen = np.float32([kp_lateral[m.trainIdx].pt for m in matches])
    destino = np.float32([kp_centro_anms[m.queryIdx].pt for m in matches])

    H, inliers = RANSAC(origen, destino, T_RANSAC, N_RANSAC)

    errors = np.linalg.norm(apply_transform(origen, H) - destino, axis=1)
    rmse = np.sqrt(np.mean(errors[inliers] ** 2))

    return H, matches, inliers, rmse


def mascara_pesos(img):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    mask[1:-1, 1:-1] = 255
    return cv2.distanceTransform(mask, cv2.DIST_L2, 5)


def generar_panoramica(img_izq_color, img_centro_color, img_der_color,
                       FACTOR=0.25, N_ANMS=400, RATIO=0.8, T_RANSAC=3, N_RANSAC=2000,
                       info=False):
    img_izq_color = cv2.resize(img_izq_color, None, fx=FACTOR, fy=FACTOR, interpolation=cv2.INTER_AREA)
    img_centro_color = cv2.resize(img_centro_color, None, fx=FACTOR, fy=FACTOR, interpolation=cv2.INTER_AREA)
    img_der_color = cv2.resize(img_der_color, None, fx=FACTOR, fy=FACTOR, interpolation=cv2.INTER_AREA)

    img_izq = cv2.cvtColor(img_izq_color, cv2.COLOR_BGR2GRAY)
    img_centro = cv2.cvtColor(img_centro_color, cv2.COLOR_BGR2GRAY)
    img_der = cv2.cvtColor(img_der_color, cv2.COLOR_BGR2GRAY)

    kp_izq_anms, des_izq_anms = features_anms(img_izq, N_ANMS)
    kp_centro_anms, des_centro_anms = features_anms(img_centro, N_ANMS)
    kp_der_anms, des_der_anms = features_anms(img_der, N_ANMS)

    H_izq_ransac, matches_izq, inliers_izq, rmse_izq = homografia_par(
        kp_izq_anms, des_izq_anms, kp_centro_anms, des_centro_anms, RATIO, T_RANSAC, N_RANSAC)
    H_der_ransac, matches_der, inliers_der, rmse_der = homografia_par(
        kp_der_anms, des_der_anms, kp_centro_anms, des_centro_anms, RATIO, T_RANSAC, N_RANSAC)

    h_izq, w_izq = img_izq.shape
    h_centro, w_centro = img_centro.shape
    h_der, w_der = img_der.shape

    corners_izq = np.array([[0, 0], [w_izq, 0], [w_izq, h_izq], [0, h_izq]])
    corners_centro = np.array([[0, 0], [w_centro, 0], [w_centro, h_centro], [0, h_centro]])
    corners_der = np.array([[0, 0], [w_der, 0], [w_der, h_der], [0, h_der]])

    all_coords = np.vstack([
        apply_transform(corners_izq, H_izq_ransac),
        corners_centro,
        apply_transform(corners_der, H_der_ransac),
    ])

    min_x = np.floor(np.min(all_coords[:, 0]))
    max_x = np.ceil(np.max(all_coords[:, 0]))
    min_y = np.floor(np.min(all_coords[:, 1]))
    max_y = np.ceil(np.max(all_coords[:, 1]))

    w_whole = np.int32(max_x - min_x)
    h_whole = np.int32(max_y - min_y)

    T = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]])

    H_izq_ransac_new = T @ H_izq_ransac
    H_der_ransac_new = T @ H_der_ransac
    H_centro = T

    imagenes = [img_izq_color, img_centro_color, img_der_color]
    homografias = [H_izq_ransac_new, H_centro, H_der_ransac_new]

    imagenes_warped = np.stack([
        cv2.warpPerspective(img, H, (w_whole, h_whole)) for img, H in zip(imagenes, homografias)
    ])
    mascaras_warped = np.stack([
        cv2.warpPerspective(mascara_pesos(img), H, (w_whole, h_whole)) for img, H in zip(imagenes, homografias)
    ])[..., None]

    numerador = (mascaras_warped * imagenes_warped).sum(axis=0)
    denominador = mascaras_warped.sum(axis=0)

    I = numerador / np.maximum(denominador, 1e-6)
    I = np.clip(I, 0, 255).astype(np.uint8)

    if not info:
        return I

    return I, {
        "tamaño": (int(w_whole), int(h_whole)),
        "H_izq": H_izq_ransac,
        "H_der": H_der_ransac,
        "matches_izq": len(matches_izq),
        "matches_der": len(matches_der),
        "inliers_izq": int(inliers_izq.sum()),
        "inliers_der": int(inliers_der.sum()),
        "rmse_izq": float(rmse_izq),
        "rmse_der": float(rmse_der),
    }
