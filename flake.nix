{
  description = "pm-ai - product-management agent skills";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    git-hooks-nix,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};

        # Tests only need the stdlib + pytest, so a Nix-provided interpreter keeps
        # the hook hermetic (it also runs inside the `nix flake check` sandbox).
        python = pkgs.python314.withPackages (ps: [ps.pytest]);

        pre-commit-check = git-hooks-nix.lib.${system}.run {
          src = ./.;
          hooks = {
            alejandra.enable = true;

            markdownlint = {
              enable = true;
              settings.configuration.MD013 = false; # skill files are prose; don't hard-wrap them at 80 columns
              settings.configuration.MD060 = false; # don't require table pipes to line up across rows
            };

            pytest = {
              enable = true;
              name = "pytest";
              entry = "${python}/bin/python -m pytest -q";
              files = "\\.py$";
              pass_filenames = false;
            };
          };
        };
      in {
        checks.pre-commit-check = pre-commit-check;

        devShells.default = pkgs.mkShell {
          name = "pm-ai";

          packages = [
            pkgs.uv
            python
          ];

          buildInputs = pre-commit-check.enabledPackages;

          shellHook = ''
            ${pre-commit-check.shellHook}
          '';
        };
      }
    );
}
