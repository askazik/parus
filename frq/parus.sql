CREATE TABLE "amplitudes" ("id_ampl" integer PRIMARY KEY  NOT NULL  DEFAULT (null) ,"ampl_frq" integer NOT NULL  DEFAULT (null) ,"number" integer NOT NULL ,"ampl_m" real NOT NULL  DEFAULT (null) ,"ampl_s" real NOT NULL  DEFAULT (null) ,"ampl_file" integer NOT NULL  DEFAULT (0) ,"height" real NOT NULL  DEFAULT (0) ,"thereshold" REAL NOT NULL  DEFAULT (0) ,"n_sigma" REAL NOT NULL  DEFAULT (0) );
CREATE TABLE files (
  id_file   integer NOT NULL DEFAULT null PRIMARY KEY,
  filename  varchar NOT NULL,
  "time"    datetime NOT NULL,
  dt        real NOT NULL DEFAULT 0,
  dh        real NOT NULL DEFAULT 0,
  notes     varchar
);
CREATE TABLE "frequencies" ("id_frq" INTEGER PRIMARY KEY  NOT NULL ,"frequency" INTEGER NOT NULL ,"notes" VARCHAR);
