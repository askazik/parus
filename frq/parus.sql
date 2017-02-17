CREATE TABLE "amplitudes" ("id_ampl" INTEGER PRIMARY KEY  NOT NULL ,"ampl_frq" INTEGER NOT NULL ,"ampl_file" INTEGER NOT NULL ,"number" INTEGER NOT NULL ,"a_eff" REAL NOT NULL  DEFAULT (null) ,"a_std" REAL NOT NULL  DEFAULT (null) ,"h_eff" REAL NOT NULL  DEFAULT (null) ,"h_std" REAL NOT NULL  DEFAULT (null) ,"n_std" REAL NOT NULL  DEFAULT (null) ,"L" REAL DEFAULT (NULL) ,"B" REAL DEFAULT (NULL) ,"H" REAL DEFAULT (NULL) );
CREATE TABLE "files" (
  	"id_file" INTEGER PRIMARY KEY NOT NULL,
  	"filename" VARCHAR(20) NOT NULL,
  	"time"    DATETIME NOT NULL,
  	"dt"      REAL NOT NULL,
  	"dh"      REAL NOT NULL,
  	"notes"   VARCHAR(100)
);
CREATE TABLE "frequencies" (
	"id_frq"  INTEGER PRIMARY KEY NOT NULL,
	"frequency" INTEGER NOT NULL,
	"B" 	  REAL DEFAULT(NULL)
);
