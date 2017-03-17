SELECT
amplitudes.ampl_file AS i_file,
amplitudes.number AS N,
frequencies.frequency AS Frq,
files.time AS Datetime,
amplitudes.height AS Height,
amplitudes.ampl_m AS Ampl, 
amplitudes.ampl_s AS A_s,
amplitudes.n_sigma AS N_s
FROM 
files, amplitudes, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
AND (i_file) IN (
SELECT 
amplitudes.ampl_file AS i_file
FROM files, amplitudes
WHERE
amplitudes.ampl_file = files.id_file
AND (TIME(files.time) >= '18:00:00' OR TIME(files.time) < '07:00:00')
GROUP BY amplitudes.ampl_file  HAVING COUNT(*)>1
)

-- Номера файлов и частот для которых найдены два первых отражения.
SELECT DISTINCT 
amplitudes.ampl_file AS i_file,
amplitudes.ampl_frq AS i_frq
FROM 
amplitudes
WHERE 
amplitudes.number == 1

-- Подсчёт B для выборок с одним отражением.
SELECT DISTINCT 
amplitudes.ampl_file AS i_file,
amplitudes.ampl_frq AS i_frq,
frequencies.frequency AS Frq,
files.time AS Datetime,
amplitudes.height AS Height,
amplitudes.ampl_m AS Ampl, 
amplitudes.ampl_s AS A_s,
1/(amplitudes.ampl_m * amplitudes.height) AS B1,
1/((amplitudes.ampl_m-amplitudes.n_sigma) * amplitudes.height) AS B2
FROM 
files, amplitudes, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
AND amplitudes.number == 0
AND (TIME(files.time) >= '18:00:00' OR TIME(files.time) < '07:00:00')

-- Подсчёт B для выборок с одним отражением и их группировка.
SELECT DISTINCT 
frequencies.frequency AS Frq,
AVG(1/(amplitudes.ampl_m * amplitudes.height)) AS B1,
AVG(1/((amplitudes.ampl_m-amplitudes.n_sigma) * amplitudes.height)) AS B2
FROM 
files, amplitudes, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
AND amplitudes.number == 0
AND (TIME(files.time) >= '18:00:00' OR TIME(files.time) < '07:00:00')
GROUP BY Frq

-- Выборки с посчитанными B
SELECT 
id_ampl, filename, time, frequency, B_with_noise, B_without_noise
FROM 
files, frequencies, amplitudes
WHERE 
files.id_file == amplitudes.ampl_file
AND frequencies.id_frq = amplitudes.ampl_frq
AND B_with_noise  <> 0
-- AND (TIME(time) >= '18:00:00' OR TIME(time) < '07:00:00')

-- Выбор частот для которых существуют расчётные постоянные аппаратуры.
-- Расчёт средних по выборке постоянных аппаратуры.
SELECT 
ampl_frq, 
AVG(B_with_noise) "Average B1", AVG(B_without_noise) "Average B2",
COUNT(*) AS Count
FROM amplitudes, files
WHERE 
amplitudes.ampl_file = files.id_file
AND B_with_noise  <> 0
AND (TIME(time) >= '18:00:00' OR TIME(time) < '07:00:00')
GROUP BY ampl_frq

-- Расчёт ро
SELECT 
amplitudes.ampl_file, amplitudes.ampl_frq, 
amplitudes.ampl_m, amplitudes.ampl_s, amplitudes.n_sigma, amplitudes.height,
avg_b1, avg_b2, Count,
avg_B1 * ampl_m * amplitudes.height AS rho1,
avg_B2 * ampl_m * amplitudes.height AS rho2
FROM
amplitudes,
(
SELECT 
ampl_frq, 
AVG(B_with_noise) AS avg_b1 , AVG(B_without_noise) AS avg_B2,
COUNT(*) AS Count
FROM amplitudes, files
WHERE 
amplitudes.ampl_file = files.id_file
AND B_with_noise  <> 0
AND (TIME(time) >= '18:00:00' OR TIME(time) < '07:00:00')
GROUP BY ampl_frq
) subquery1
WHERE
amplitudes.ampl_frq = subquery1.ampl_frq
AND amplitudes.number == 0
AND Count > 10
AND n_sigma > 0
ORDER BY rho1

-- L B H
SELECT
time, frequency, ampl_m, ampl_s, n_sigma, L, amplitudes.B, H
FROM 
amplitudes, files, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
--AND (TIME(files.time) BETWEEN '00:00:00' AND '08:00:00' OR TIME(files.time) BETWEEN '18:00:00' AND '23:59:59')
AND H > 80 AND L > 0 AND ampl_s > n_sigma
ORDER BY
frequency

--- 15/03/2017
SELECT
amplitudes.ampl_file AS i_file,
frequencies.frequency AS Frq,
files.time AS Datetime,
amplitudes.h0_eff AS H1,
amplitudes.h1_eff AS H2,
amplitudes.power0 AS P1, 
amplitudes.power1 AS P2,
amplitudes.Pnoise AS Pn,
(amplitudes.power0 - amplitudes.power1) AS rho 
FROM 
files, amplitudes, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
AND amplitudes.power1 > amplitudes.Pnoise + 3
AND amplitudes.power0 > 80
AND (amplitudes.power0 - amplitudes.power1)  > 10

--- 17/03/2017
SELECT
amplitudes.ampl_file AS i_file,
frequencies.frequency AS Frq,
files.time AS Datetime,
amplitudes.h0_eff AS H1,
amplitudes.h1_eff AS H2,
amplitudes.h1_eff-amplitudes.h0_eff AS H,
amplitudes.power0 AS P1, 
amplitudes.power1 AS P2,
amplitudes.Pnoise AS Pn,
(amplitudes.power0 - amplitudes.power1 - 6) AS rho,
amplitudes.count AS count
FROM 
files, amplitudes, frequencies
WHERE 
amplitudes.ampl_file = files.id_file
AND amplitudes.ampl_frq = frequencies.id_frq
AND amplitudes.power1 > amplitudes.Pnoise + 3 --- наблюдается превышение шума сигналом
AND Datetime < '2016-12-07 09:00:00' --- измерение на старую антенну
AND Frq >= 1400 --- всё, что более гирочастоты
AND count < 9 --- реально наблюдаемые отражения
AND count == 1 --- наблюдается два отражения
