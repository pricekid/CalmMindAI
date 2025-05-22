{pkgs}: {
  deps = [
    pkgs.zip
    pkgs.lsof
    pkgs.libuuid
    pkgs.postgresql
    pkgs.openssl
  ];
}
