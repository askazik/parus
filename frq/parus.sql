CREATE TABLE amplitudes (
  id_ampl    integer NOT NULL DEFAULT null PRIMARY KEY,
  ampl_frq   integer NOT NULL DEFAULT null,
  number     integer NOT NULL,
  ampl_m     real NOT NULL DEFAULT null,
  ampl_s     real NOT NULL DEFAULT null,
  ampl_file  integer NOT NULL DEFAULT 0,
  heights_m  real NOT NULL DEFAULT 0,
  heights_s  real NOT NULL DEFAULT 0, "thereshold" REAL NOT NULL  DEFAULT 0,
  /* Foreign keys */
  CONSTRAINT amplitude_frq
    FOREIGN KEY (ampl_file)
    REFERENCES files(id_file)
    ON DELETE CASCADE
    ON UPDATE CASCADE, 
  CONSTRAINT amplitude_frq
    FOREIGN KEY (ampl_frq)
    REFERENCES frequencies(id_frq)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
CREATE TABLE files (
  id_file   integer NOT NULL DEFAULT null PRIMARY KEY,
  filename  varchar NOT NULL,
  "time"    datetime NOT NULL,
  dt        real NOT NULL DEFAULT 0,
  dh        real NOT NULL DEFAULT 0,
  notes     varchar
);
CREATE TABLE "frequencies" ("id_frq" INTEGER PRIMARY KEY  NOT NULL ,"frequency" INTEGER NOT NULL ,"notes" VARCHAR);
