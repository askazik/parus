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