# 📂 Local Media Organizer Utility

> 🇪🇸 [Leer en Español](README.es.md)

## 🎯 Project Objective

Create a simple and robust local desktop application designed to automate the organization of media files (photos and videos) from a source path to a destination path. The sorting criterion is the **creation/capture date** of the files, ensuring **data integrity** during the collection process and keeping the source path clean.

**Organization Example:**

- **Input Path:** `H:\DCIM\12312\`
- **Output Path:** `C:\photos\`
- **Final Structure:**
  ```
  C:\photos\
  ├── 2019\
  │   ├── 01-January\
  │   └── 02-February\
  └── 2020\
      └── 03-March\
  ```

---

## 🚀 Quick Start

### For Users (Pre-compiled Executable)

1. Download the latest `.exe` from [Releases](https://github.com/slider66/OrdenaFotos/releases)
2. Run `OrdenaFotos_Pro.exe`
3. Select source and destination folders
4. Click "INICIAR ORGANIZACIÓN"

> [!NOTE]
> Windows may show a security warning since the app is not digitally signed. Click **"More info"** → **"Run anyway"** to proceed.

### For Developers (Build from Source)

**Prerequisites:**

- **Python 3.10+** installed and added to PATH
- **Git** (to clone the repository)

**Steps:**

1. **Clone the repository:**

   ```bash
   git clone https://github.com/slider66/OrdenaFotos.git
   cd OrdenaFotos
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   Dependencies installed:

   - `Pillow` - Image processing and EXIF reading
   - `ExifRead` - Additional EXIF metadata extraction
   - `ttkbootstrap` - Modern UI theme
   - `pyinstaller` - Executable compilation

3. **Run the application:**

   ```bash
   python main_gui.py
   ```

4. **Build executable (Optional):**

   ```bash
   build_executable.bat
   ```

   The compiled `.exe` will be in `dist/OrdenaFotos_Pro.exe`

---

## 🛠️ Recommended Tech Stack

The project relies on **Python 3.x** due to its simplicity, maturity in file system handling, and powerful libraries available for metadata extraction.

| Component                | Module/Library           | Specific Purpose                                         |
| :----------------------- | :----------------------- | :------------------------------------------------------- |
| **Base Language**        | Python 3.x               | Implementation of all logic.                             |
| **File Handling**        | `pathlib`, `shutil`      | Recursive search, directory creation, and file movement. |
| **Metadata Extraction**  | `Pillow` (or `ExifRead`) | Reading EXIF data to determine photo capture date.       |
| **Interface (Optional)** | Tkinter / Flet           | User interface for path selection.                       |

---

## 🔑 Key Functional Logic

### 1. Date Extraction and Prioritization (EXIF)

To ensure the **most consistent date** and correctly order files, the following prioritization logic applies:

1.  **Priority 1 (Metadata):** Attempt to extract the capture/creation date from **EXIF** metadata (for photos) or video tags.
2.  **Priority 2 (File System - Creation):** If no valid internal metadata exists, use the file's **creation date** registered by the operating system.
3.  **Priority 3 (File System - Modification):** If previous dates are inaccessible or inconsistent (e.g., on systems where creation date is lost), use the **last modification date**.

The resulting date constructs the folder structure `Year/Month Name`.

### 2. Safe Movement and File Validation

To prevent data loss, the transfer process must be **atomic** (or simulate it with strict validation).

- **Step 1: Movement:** Use `shutil.move()` (or copy+delete) to transfer the file to the destination.
- **Step 2: Existence Validation:** Immediately check that the file exists at the **destination path**.
- **Step 3: Integrity Validation:** Verify that the **file size** at the destination **exactly matches** the original file size.
- **Step 4: Confirmation:** **Only if existence and integrity (size) are validated**, the process is considered successful. If validation fails, an error is logged, and the file remains at the source.

### 3. Empty Folder Cleanup Logic

Once all files are processed and moved, a cleanup process runs on the input path to remove unnecessary clutter.

- **Reverse Recursive Sweep:** Recursively traverse all folders and subfolders of the **input path**, starting from the deepest directories.
- **Empty Check:** Use `os.listdir()` to verify if the folder is completely empty.
- **Deletion:** If the folder is empty, it is removed (`os.rmdir()`). This ensures only empty directory structures are removed, leaving the source path organized and clean.

---

## 💾 Multimedia File Support (Images and Video)

The application identifies and processes an exhaustive list of common file formats, RAW, and sidecar files used by key manufacturers like Apple (iPhone) and Sony.

### A. Common Image Extensions

| Type                                | Extensions                                                                                                           |
| :---------------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| **Standard**                        | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.webp`                                                    |
| **High Efficiency (Apple/General)** | `.heic`, `.heif` (Modern high-compression formats).                                                                  |
| **Professional / RAW**              | `.dng`, `.cr2`, `.cr3` (Canon), `.nef` (Nikon), **`.arw` (Sony)**, `.raf` (Fuji), `.orf` (Olympus), `.pef` (Pentax). |

### B. Common Video Extensions

| Type                       | Extensions                                                                                           |
| :------------------------- | :--------------------------------------------------------------------------------------------------- |
| **Standard**               | `.mp4`, `.mov` (Apple native), `.avi`, `.mkv`, `.wmv` (Windows).                                     |
| **High Efficiency (HEVC)** | High-efficiency video files usually use **`.mp4`** or **`.mov`** containers with H.265 (HEVC) codec. |

### C. Auxiliary Files (Sidecar)

These files contain editing metadata or support info and must be **moved along with their main file** (e.g., move `photo.heic` and `photo.aae` to the same destination folder).

- **`.aae`**: Apple photo editing files (iPhone/iPad).
- **`.xmp`**: General editing metadata (Adobe, used in RAW).
- **`.thm`**: Thumbnail files associated with camera videos.

---

## 💎 Duplicate Handling (HASH Validation)

To ensure only true duplicates (same content) are managed, integrity checking via **hashing algorithms** is applied.

### Check Flow

1.  **HASH Calculation:** When finding a file in the **Input Path** (`Source`) that has the **same name** as an existing file in the **Output Path** (`Destination`), the application calculates the **cryptographic HASH** (e.g., SHA-256) of both files.
2.  **Verification:**
    - If **HASH(Source) == HASH(Destination)**: The file is an exact duplicate.
    - If **HASH(Source) != HASH(Destination)**: Files are different (despite same name), and the source file must be renamed (e.g., add suffix `_dup_1`).
3.  **Actions for Exact Duplicates (Matching HASH):**

In the current version (`v1.0+`), the application prioritizes safety:

- **Exact Duplicates (Identical Hash):** The file is moved to a special folder `_DUPLICADOS_REVISAR` (Duplicates to Review) in the destination.
- **Name Collision (Different Hash):** **AUTOMATIC RENAMING** applies (`file_dup_N.ext`).
- **Delete Original:** For safety, originals are never automatically deleted without validation.

## 🌟 New Features

### 📁 Folder Exclusion (v2.1)

Exclude specific folders from scanning to avoid processing unwanted files.

**Features:**

- **Visual Interface:** Dedicated section with listbox showing excluded folders
- **Easy Management:** Add/Remove buttons with multi-select support (Ctrl+Click, Shift+Click)
- **Optional Persistence:** Checkbox to save exclusions between sessions
- **Performance:** Folders are filtered during scan (not accessed at all)
- **Ghost File Prevention:** Automatically skips broken symlinks and non-existent files

**Use Cases:**

- Exclude backup folders
- Skip cloud sync directories (Dropbox, OneDrive)
- Ignore system folders
- Exclude temporary or processed photo folders
- Skip social media downloads (WhatsApp, Instagram)

**How to Use:**

1. Click "➕ Add" button in "Excluded Folders" section
2. Select folder to exclude
3. (Optional) Enable "Save exclusions between sessions" to persist
4. Selected folders and all their subfolders will be skipped during organization

### 🧪 Simulation Mode (Dry Run)

Check the **"Modo Simulación"** (Simulation Mode) box to run the analysis without moving a single file.

- Verify what would happen.
- Generate full logs.
- Perfect for gaining confidence before organizing.

### 📝 Persistent Logs and Viewer

- **History:** Each run generates an `operaciones_DATE.log` file in the destination folder.
- **"Open Log" Button:** Upon completion, press this button to view the immediate report without manually searching for the file.

## 🕵️ Duplicate Finder (v2.0)

A new tab dedicated exclusively to deep cleaning.

1.  **Select a folder** (e.g., an external hard drive).
2.  **The program scans** all content looking for byte-for-byte identical files (SHA-256).
3.  **Automatic Action:**
    - Keeps **one** original (shortest path).
    - Moves **all** excess copies to a `_DUPLICADOS` folder in the analysis root.
4.  **Result:** You can safely delete the contents of `_DUPLICADOS` knowing a safe copy exists in its original place.

---

## 🚀 Compilation and Execution

If you wish to generate your own `.exe` from source code, an automated Windows script is included.

### Prerequisites

- Have **Python 3.x** installed and added to PATH.
- (Optional) An active virtual environment, though the script handles dependencies.

### Compilation Steps

1.  Open the project folder.
2.  Double click on **`build_executable.bat`**.
3.  The script will automatically install necessary dependencies (`Pillow`, `ttkbootstrap`, `pyinstaller`, etc.).
4.  Upon completion, you will find the new executable in **`dist/OrdenaFotos_Pro.exe`**.

### Execution

Simply open the generated `.exe` file.

> [!WARNING] > **Windows blocks execution?**
> Since it's not digitally signed (expensive), Windows Defender may show "Windows protected your PC".
>
> 1. Click **"More info"**.
> 2. Click **"Run anyway"**.
>
> **Alternative (Permanent Unblock):**
>
> 1. Right-click the `.exe` > Properties.
> 2. Check the **"Unblock"** box at the bottom right.
> 3. Apply and OK.

---

## 🛡️ Reliability and Tests

This application has undergone a battery of automated tests to guarantee file safety.

### ✅ Test Coverage

1. **Data Integrity:** Verified that `SHA-256` calculation detects 1-byte differences and exact matches.
2. **Date Priority:** Verified correct fallback: _EXIF > Creation > Modification_.

### 3. Duplicate Management 👯

- **Name Collision (Different Content):** If file exists but is different, it is automatically renamed (e.g., `photo_dup_1.jpg`) and saved alongside the original.
- **Exact Duplicate (Same Content):** If file exists and is identical (SHA-256 verified), the new file is **MOVED** to a special folder named `_DUPLICADOS_REVISAR` within the destination.
  - This allows you to manually review and delete duplicates without fear of losing anything.
  - Nothing is automatically overwritten.

4. **Loop Resilience:**
   - Detects if source and destination are the same physical path (Idempotency) and skips it.
   - Stops infinite loops if destination folder is inside source.
5. **Non-Destructive:** Confirmed that source is NEVER deleted without first validating existence and byte-to-byte size in destination.

# OrdenaFotos
