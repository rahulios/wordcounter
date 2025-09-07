# Word Counter Pro - Cloud Sync Features

## Overview

This document describes the cloud synchronization features added to Word Counter Pro, enabling users to sync their writing data across multiple devices and access it from anywhere.

## 🚀 New Features

### 1. User Authentication
- **User Registration**: Create new accounts with email and username
- **Secure Login**: Password-based authentication with encryption
- **Account Management**: View profile, subscription status, and sync history
- **Session Persistence**: Stay logged in across app restarts

### 2. Cloud Data Synchronization
- **Real-time Sync**: Automatic synchronization every 5 minutes
- **Manual Sync**: Force sync on demand
- **Conflict Resolution**: Smart handling of data conflicts
- **Offline Mode**: Continue working offline, sync when connected

### 3. Data Security
- **End-to-End Encryption**: All data encrypted before cloud storage
- **Password-based Keys**: Encryption keys derived from user passwords
- **Local Key Storage**: Secure local storage of encryption keys
- **No Plain Text**: Never store unencrypted data in the cloud

### 4. Enhanced User Interface
- **Sync Status Widget**: Real-time sync status display
- **Account Menu**: Easy access to account management
- **Cloud Menu**: Dedicated cloud sync controls
- **Status Notifications**: Visual feedback for sync operations

## 📁 File Structure

```
WordCounter/
├── cloud_sync.py              # Core cloud sync functionality
├── auth_ui.py                 # Authentication UI components
├── cloud_integration.py       # Integration with main app
├── wordcounter_with_cloud.py  # Enhanced main application
├── backend_server.py          # Local testing server
├── setup_cloud_sync.py        # Setup wizard
└── CLOUD_SYNC_README.md       # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- All existing Word Counter Pro dependencies
- Internet connection for cloud sync

### Quick Setup
1. **Run the setup wizard**:
   ```bash
   python setup_cloud_sync.py
   ```

2. **Install dependencies** (if not done by setup wizard):
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server** (for testing):
   ```bash
   python backend_server.py
   ```

4. **Launch the enhanced app**:
   ```bash
   python wordcounter_with_cloud.py
   ```

### Manual Setup
1. Install additional dependencies:
   ```bash
   pip install requests cryptography
   ```

2. Start the backend server in a separate terminal:
   ```bash
   python backend_server.py
   ```

3. Launch the enhanced application:
   ```bash
   python wordcounter_with_cloud.py
   ```

## 🔧 Configuration

### Cloud Sync Settings
Access sync settings through: **Cloud → Sync Settings**

- **Auto-sync**: Enable/disable automatic synchronization
- **Sync Interval**: Set sync frequency (default: 5 minutes)
- **Data Types**: Choose what data to sync
  - Writing sessions
  - Goals and achievements
  - Application settings

### Account Settings
Access account settings through: **Account → Account Management**

- **Profile Information**: View username, email, subscription tier
- **Sync Status**: Check connection and last sync time
- **Manual Sync**: Force immediate synchronization
- **Logout**: Sign out of cloud account

## 🔐 Security Features

### Data Encryption
- **AES-256 Encryption**: Industry-standard encryption algorithm
- **PBKDF2 Key Derivation**: Secure key generation from passwords
- **Salt-based Hashing**: Protection against rainbow table attacks
- **Local Key Storage**: Encryption keys never transmitted

### Privacy Protection
- **No Data Mining**: We don't analyze your writing content
- **Local Processing**: All analytics done on your device
- **Encrypted Storage**: Data encrypted before cloud transmission
- **User Control**: Full control over what data is synced

### Network Security
- **HTTPS Only**: All communication encrypted in transit
- **Token-based Auth**: Secure authentication without password storage
- **Request Validation**: Server-side validation of all requests
- **Rate Limiting**: Protection against abuse

## 📊 Data Synchronization

### What Gets Synced
- **Writing Sessions**: Date, word count, duration, WPM, productivity score
- **Goals**: Writing goals, progress, deadlines
- **Achievements**: Unlocked achievements and progress
- **Settings**: Application preferences and configuration

### What Doesn't Get Synced
- **Raw Text Content**: Only statistics are synced, not actual text
- **Local Files**: Excel files and backups remain local
- **Sensitive Data**: Passwords, personal information
- **Temporary Data**: Cache files and temporary data

### Sync Process
1. **Data Preparation**: Collect and format local data
2. **Encryption**: Encrypt data using user's key
3. **Upload**: Send encrypted data to cloud server
4. **Verification**: Confirm successful upload
5. **Local Update**: Update local sync timestamp

## 🌐 Backend Server

### Local Testing Server
The included `backend_server.py` provides a local testing environment:

- **Flask-based**: Simple HTTP server for development
- **In-memory Storage**: Data stored in memory (not persistent)
- **REST API**: Standard REST endpoints for all operations
- **CORS Support**: Cross-origin request support

### API Endpoints
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /sync/upload` - Upload sync data
- `GET /sync/download/<user_id>` - Download sync data
- `GET /user/<user_id>/profile` - Get user profile
- `GET /health` - Health check

### Production Deployment
For production use, consider:
- **Database**: PostgreSQL or MongoDB for persistent storage
- **Authentication**: JWT tokens or OAuth2
- **Load Balancing**: Multiple server instances
- **Monitoring**: Application performance monitoring
- **Backup**: Regular database backups

## 🚀 Usage Guide

### First Time Setup
1. **Launch the app**: Run `python wordcounter_with_cloud.py`
2. **Create account**: Click Account → Register
3. **Fill details**: Enter email, username, password
4. **Start writing**: Begin your first writing session
5. **Auto-sync**: Data syncs automatically every 5 minutes

### Daily Usage
1. **Login**: App remembers your session
2. **Write normally**: Use the app as usual
3. **Monitor sync**: Check sync status in the status bar
4. **Manual sync**: Use "Sync Now" if needed
5. **Account management**: Access through Account menu

### Multi-Device Usage
1. **Install on second device**: Copy app to another computer
2. **Login with same account**: Use your credentials
3. **Data syncs automatically**: All data appears on new device
4. **Continue writing**: Seamless experience across devices

## 🔧 Troubleshooting

### Common Issues

#### "Cannot connect to server"
- **Check internet connection**: Ensure you're online
- **Verify server running**: Backend server must be running
- **Check firewall**: Ensure port 5000 is accessible
- **Try manual sync**: Use "Sync Now" button

#### "Login failed"
- **Check credentials**: Verify username/password
- **Check server**: Ensure backend server is running
- **Reset password**: Contact support if needed
- **Create new account**: Try registering again

#### "Sync failed"
- **Check connection**: Ensure stable internet
- **Try manual sync**: Use "Sync Now" button
- **Check server logs**: Look for error messages
- **Restart app**: Close and reopen the application

#### "Data not syncing"
- **Check sync settings**: Verify auto-sync is enabled
- **Check data types**: Ensure desired data is selected
- **Manual sync**: Try forcing a manual sync
- **Check logs**: Look for error messages in console

### Debug Mode
Enable debug logging by setting environment variable:
```bash
set WORDCOUNTER_DEBUG=1
python wordcounter_with_cloud.py
```

### Log Files
Check these files for error information:
- `word_counter.log` - Application logs
- Console output - Real-time error messages
- Server logs - Backend server output

## 🔮 Future Enhancements

### Planned Features
- **Real-time Collaboration**: Multiple users editing simultaneously
- **Version History**: Track changes over time
- **Advanced Analytics**: Cloud-based analytics and insights
- **Mobile App**: Cross-platform mobile application
- **API Integration**: Connect with other writing tools

### Enterprise Features
- **Team Management**: Multi-user team accounts
- **Admin Dashboard**: Centralized management interface
- **Custom Domains**: White-label solutions
- **SSO Integration**: Single sign-on support
- **Advanced Security**: Enterprise-grade security features

## 📞 Support

### Getting Help
- **Documentation**: Check this README and inline help
- **GitHub Issues**: Report bugs and request features
- **Email Support**: Contact support@wordcounterpro.com
- **Community Forum**: Join our user community

### Contributing
- **Bug Reports**: Help us fix issues
- **Feature Requests**: Suggest new features
- **Code Contributions**: Submit pull requests
- **Documentation**: Help improve documentation

## 📄 License

This cloud sync functionality is part of Word Counter Pro and is subject to the same license terms as the main application.

---

**Note**: This is a development version of the cloud sync features. For production use, additional security measures and testing are recommended.
