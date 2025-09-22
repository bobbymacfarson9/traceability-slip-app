# OneDrive Integration Setup

## 🎯 What This Gives You

- **Direct access** to your company's OneDrive loading slip files
- **Automatic updates** when new orders come in
- **No manual file transfers** needed
- **Real-time sync** with the office

## 🔧 Setup Steps

### 1. Register an Azure AD App

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: `Traceability Slip App`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: `https://your-domain.com/auth/callback` (or use a localhost URL for testing)

### 2. Configure API Permissions

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Delegated permissions**
5. Add these permissions:
   - `Files.Read`
   - `User.Read`
6. Click **Grant admin consent**

### 3. Get Your Client ID

1. In your app registration, go to **Overview**
2. Copy the **Application (client) ID**
3. Update the `ONEDRIVE_CLIENT_ID` in `src/lib/onedrive.ts`

### 4. Update the App Configuration

Replace `your-client-id-here` in these files:
- `src/lib/onedrive.ts` (line 4)
- `src/components/OneDriveAuth.tsx` (line 25)

### 5. Set Up OneDrive Folder Structure

Create a folder in your company OneDrive called:
```
/Loading Slips/
```

Place your loading slip files in this folder.

## 📱 How It Works

1. **First time**: User taps "Connect OneDrive" and signs in
2. **App loads**: All Excel files from `/Loading Slips/` folder
3. **User selects**: Any file from the list
4. **Auto-updates**: App can refresh to get latest files
5. **Real-time**: New orders appear automatically

## 🔄 Auto-Update Workflow

```typescript
// The app can check for updates periodically
const checkForUpdates = async () => {
  const latestFile = await getLatestLoadingSlip();
  if (latestFile.name !== currentFileName) {
    // New file available - notify user
    Alert.alert('New Loading Slip', 'A new loading slip is available. Load it now?');
  }
};
```

## 🛡️ Security Features

- **OAuth 2.0** authentication
- **Read-only access** to files
- **Company directory only** (no personal accounts)
- **Secure token storage**

## 🚀 Benefits

- **No manual file transfers**
- **Always up-to-date** with latest orders
- **Works offline** once file is loaded
- **Automatic sync** when new orders come in
- **Company-wide access** for all authorized users

## 🔧 Troubleshooting

**"Not authenticated" error:**
- Check that the client ID is correct
- Verify API permissions are granted
- Ensure admin consent was given

**"Failed to load files" error:**
- Check internet connection
- Verify the `/Loading Slips/` folder exists
- Ensure user has access to the folder

**Files not showing:**
- Check that files are `.xlsx` or `.xls` format
- Verify files are in the correct folder
- Try refreshing the OneDrive connection
