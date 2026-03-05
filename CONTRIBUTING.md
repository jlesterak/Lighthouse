# Contributing to Lighthouse

First off, thank you for considering contributing to Lighthouse! It's people like you that make Lighthouse a reliable, comprehensive tool for off-grid survival and knowledge preservation.

## How Can I Contribute?

### 1. Recommending New Knowledge Repositories

Lighthouse relies on high-quality, Free and Open Source datasets (primarily in the ZIM format). If you know of an excellent resource for off-grid living, computing, emergency medicine, survival, ham radio, or similar topics, please propose it!

**To add a resource:**
1. Ensure the resource is legally distributable (Public Domain, Creative Commons, GPL, etc.).
2. Locate a reliable download link (preferably a ZIM file from Kiwix).
3. Open a Pull Request adding the new entry to our `manifest.json`.

### 2. Improving the Custom Live OS

Lighthouse includes a customized, Debian-based Live Linux environment built with `live-build`. Contributions here are highly welcome:
- Stripping down the OS size (removing unnecessary packages).
- Adding crucial open-source tools to the default XFCE desktop environment.
- Improving the auto-mount scripts for the exFAT data partition.

**To improve the Live OS:**
1. Fork the repository and modify the files within the `LiveOS/` directory.
2. Build the ISO locally to test your changes using the [Build Guide](docs/build_guide.md).
3. Submit a Pull Request with your changes and a description of *why* they are necessary.

### 3. Enhancing the Cross-Platform Updater

The `updater.py` tool must remain dependency-free (using only Python's standard library) so it can run flawlessly on Windows, Mac, Linux, and Android (via Termux). 

**To improve the Updater:**
- Add stronger error checking.
- Improve the CLI interface or progress bar logic.
- Optimize the chunked downloading logic (`Range` HTTP header handling) for highly unstable internet connections.

### 4. Documentation

Documentation is the lifeblood of this project. If you find a typo, an unclear sentence, or want to write an entirely new tutorial on how to flash the Lighthouse ISO from Windows, please do!

## Submitting a Pull Request

1. Fork the repository on GitHub.
2. Create a new branch specifically for your feature or bug fix (`git checkout -b feature/my-new-feature`).
3. Make your changes in your forked repository.
4. Test your changes thoroughly. If you touched `manifest.json`, verify that `updater.py` still parses it correctly.
5. Push your branch to GitHub (`git push origin feature/my-new-feature`).
6. Open a Pull Request against the main branch of the Lighthouse repository. Ensure your PR description clearly explains what you changed and why.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone.
