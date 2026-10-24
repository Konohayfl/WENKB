CREATE TABLE IF NOT EXISTS "t_sys_user" (
  "user_id" text(32) NOT NULL,
  "username" varchar(128) NOT NULL,
  "nickname" varchar(80) NOT NULL,
  "password_hash" varchar(256) NOT NULL,
  "status" varchar(1) NOT NULL DEFAULT 'Y',
  "crt_tm" varchar(19) NOT NULL,
  PRIMARY KEY ("user_id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "uq_sys_user_username"
ON "t_sys_user" ("username");
