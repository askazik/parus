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