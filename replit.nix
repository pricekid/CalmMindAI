{pkgs}: {
  deps = [
    pkgs.lsof
    pkgs.libuuid
    pkgs.postgresql
    pkgs.openssl
  ];
}
