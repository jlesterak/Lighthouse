# How to Use Lighthouse

The Lighthouse USB is primarily designed to be plugged into any available device during an emergency or off-grid scenario, instantly granting access to its stored knowledge.

There are **three** main ways to use Lighthouse:

## 1. Using it on an existing Windows, Mac, or Linux Computer

If you have a functioning laptop or desktop computer running its normal operating system, you do not need to boot from the USB.

1. **Plug in the USB Drive.**
2. Ignore any prompts from Windows asking to "format" the drive. This is just Windows not recognizing the bootable Linux partition.
3. Open your File Explorer and navigate to the USB drive (it should be labeled `LIGHTHOUSE`).
4. **Open the Readers Folder:**
   - **Windows:** Double-click `readers/windows/kiwix-desktop.exe`. It runs without installation. If Windows
     complains about a missing `VCRUNTIME` or `MSVCP` DLL, run `vc_redist.x64.exe` from the same folder once.
   - **Mac:** No Mac reader ships on the stick (Kiwix for macOS comes from the App Store). Install it while you
     still have internet, or browse the library from another device running `kiwix-serve` (see below).
   - **Linux:** Double-click `readers/kiwix-desktop.AppImage` (mark it executable first; older distros may need
     the `libfuse2` package).
5. **Open Content:** In Kiwix, use "File > Open File", go to `content/` on the stick, and pick a `.zim` file
   (e.g. `wikipedia_en_all_maxi_2026-08.zim`).
6. You can now search and browse the entire repository!

## 2. Using it on an Android Phone or Tablet

If the power is out, smartphones and tablets are often the most viable devices due to their low power draw and internal batteries.

1. **Plug in the USB Drive using an OTG Adapter.**
   - Most modern Android phones come with a USB-C to USB-A adapter. If not, you will need to acquire one for your emergency kit.
2. Android will recognize the `exFAT` partition. Follow the prompt to "Explore" the drive using your standard file manager.
3. **Install the Reader:** Navigate to `readers/kiwix-android.apk` and tap it.
   - *Note: Android may warn you about installing apps from "Unknown Sources." You must allow this in your device settings to proceed.*
4. Open the installed **Kiwix** app.
5. Tap the menu, select "Device Storage," and navigate to your `LIGHTHOUSE` USB drive.
6. Select the `.zim` file you wish to open.
   - If Kiwix can't see the USB drive (some Android versions hide OTG storage from apps), copy the `.zim` from
     the stick to the phone's storage with the file manager and open it from there.

## 3. Booting directly from the USB (The Live OS)

If you find a functional PC but its internal hard drive is broken, corrupted, or missing, Lighthouse contains an entire, lightweight Linux operating system.

1. Shut down the computer.
2. Plug in the Lighthouse USB drive.
3. Turn on the computer and immediately press the **Boot Menu Key**. (Usually `F12`, `F8`, `F2`, `Del`, or `Esc` depending on the manufacturer).
4. Select your "USB HDD" or "UEFI USB Flash Drive" from the list.
5. After 5 seconds the default entry boots by itself into the Debian Live OS desktop. (The "failsafe" entry
   boots a clean session that ignores saved settings; use it if the normal one misbehaves.)
6. On the desktop, double-click the **"Lighthouse_Knowledge_Base"** shortcut. The data partition is mounted automatically at `/media/LighthouseData`.
7. Open a `.zim` from `content/` with Kiwix (in the applications menu).

Settings you change in the Live OS (Wi-Fi passwords, desktop settings, packages you install) are kept on the
stick's `persistence` partition and survive a reboot.

**Sharing the library with phones:** in a terminal on the Live OS, run
`kiwix-serve --port 8080 /media/LighthouseData/content/*.zim`, then open `http://<this PC's IP>:8080` in a
browser on any phone or laptop on the same network.

---

## Keeping Lighthouse Updated

Knowledge goes stale. Before you pack Lighthouse away, or during off-grid internet access windows, you should keep the `.zim` files up-to-date.

### The Unified Setup Script

The easiest way to update or interact with Lighthouse is via the unified setup script. Open a terminal (Mac/Linux) or WSL (Windows) and run:

```bash
bash <(curl -sL https://raw.githubusercontent.com/jlesterak/Lighthouse/master/setup.sh)
```

1. Select Option **1** from the menu to launch the ZIM downloader.
2. Follow the on-screen menu to select the specific files you wish to update, such as offline Wikipedia, Medical Libraries, or OpenStreetMap.
3. If the connection drops, the updater retries on its own (backing off up to a minute between tries) and resumes from the exact byte it stopped at. If it gives up, or you press Ctrl+C, just run it again later and select the same file: it resumes from the `.part` file using the HTTP `Range` header.

You can also run the updater directly via `python3 updater.py` if you prefer bypassing the menu.
