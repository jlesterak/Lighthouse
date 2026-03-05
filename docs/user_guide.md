# How to Use Lighthouse

The Lighthouse USB is primarily designed to be plugged into any available device during an emergency or off-grid scenario, instantly granting access to its stored knowledge.

There are **three** main ways to use Lighthouse:

## 1. Using it on an existing Windows, Mac, or Linux Computer

If you have a functioning laptop or desktop computer running its normal operating system, you do not need to boot from the USB.

1. **Plug in the USB Drive.**
2. Ignore any prompts from Windows asking to "format" the drive. This is just Windows not recognizing the bootable Linux partition.
3. Open your File Explorer and navigate to the USB drive (it should be labeled `LIGHTHOUSE_DATA`).
4. **Open the Readers Folder:**
   - **Windows:** Double-click on `readers/kiwix-desktop.exe`. It will launch immediately without needing installation.
   - **Mac:** Copy the Kiwix `.dmg` file to your Mac (if downloaded) and install it.
   - **Linux:** Double-click on `readers/kiwix-desktop.AppImage` (ensure it is marked as executable).
5. **Open Content:** Inside the Kiwix application, go to "File > Open File", navigate to `content/` on your USB stick, and select a `.zim` file (e.g., `wikipedia_en_all_maxi_2024-01.zim`).
6. You can now search and browse the entire repository!

## 2. Using it on an Android Phone or Tablet

If the power is out, smartphones and tablets are often the most viable devices due to their low power draw and internal batteries.

1. **Plug in the USB Drive using an OTG Adapter.**
   - Most modern Android phones come with a USB-C to USB-A adapter. If not, you will need to acquire one for your emergency kit.
2. Android will recognize the `exFAT` partition. Follow the prompt to "Explore" the drive using your standard file manager.
3. **Install the Reader:** Navigate to `readers/kiwix-android.apk` and tap it.
   - *Note: Android may warn you about installing apps from "Unknown Sources." You must allow this in your device settings to proceed.*
4. Open the installed **Kiwix** app.
5. Tap the menu, select "Device Storage," and navigate to your `LIGHTHOUSE_DATA` USB drive.
6. Select the `.zim` file you wish to open.

## 3. Booting directly from the USB (The Live OS)

If you find a functional PC but its internal hard drive is broken, corrupted, or missing, Lighthouse contains an entire, lightweight Linux operating system.

1. Shut down the computer.
2. Plug in the Lighthouse USB drive.
3. Turn on the computer and immediately press the **Boot Menu Key**. (Usually `F12`, `F8`, `F2`, `Del`, or `Esc` depending on the manufacturer).
4. Select your "USB HDD" or "UEFI USB Flash Drive" from the list.
5. The Debian Live OS will load to a desktop environment. 
6. On the desktop, double-click the **"Offline Knowledge Base"** icon. Ensure the `LIGHTHOUSE_DATA` partition is mounted via the file manager first!

---

## Keeping Lighthouse Updated

Knowledge goes stale. Before you pack Lighthouse away, or during off-grid internet access windows, you should keep the `.zim` files up-to-date. The custom python updater tool is built to handle poor internet connections and can perfectly resume large file downloads when your connection drops.

### Running the cross-platform updater

You must have Python 3 installed on your system.
**(Windows Users: Download Python from the Microsoft Store or Python.org)**

1. Plug the USB stick into your computer.
2. Open a Terminal (Linux/Mac) or Command Prompt (Windows).
3. Navigate to the USB stick, into the `updater` directory:
   ```bash
   cd D:\updater
   ```
   *(Replace `D:` with your actual USB drive letter)*
4. Run the tool:
   ```bash
   python3 updater.py
   ```
5. Follow the on-screen menu to select the specific files you wish to update.
6. If the download stalls or crashes, **do not panic**. Wait for your internet to return, run `python3 updater.py` again, and select the same file. It will instantly resume from its exact stopping point using the HTTP `Range` header.
