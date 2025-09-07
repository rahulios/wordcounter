# Security Features for Word Counter Application

## Overview

The Word Counter application now includes comprehensive security features to prevent accidental logging of sensitive information such as passwords, credit card numbers, and other private data.

## Security Options Implemented

### 1. Application Exclusion List (Primary Protection)

**How it works:**
- Automatically detects when you're using applications that typically contain sensitive data
- Pauses word counting when these applications are active
- Prevents any keystroke logging in excluded applications

**Default Excluded Applications:**
- **Browsers**: Chrome, Firefox, Edge, Safari, Brave, Opera
- **Email Clients**: Outlook, Thunderbird, Mail
- **Communication Apps**: Teams, Slack, Discord, Zoom
- **SSH Clients**: PuTTY, MobaXterm, SecureCRT
- **VPN Clients**: VPN, OpenVPN, NordVPN
- **Password Managers**: KeePass, 1Password, LastPass, Bitwarden
- **Command Line**: CMD, PowerShell, Terminal
- **Remote Desktop**: RDP, MSTSC
- **Crypto Wallets & Financial Apps**: MetaMask, Phantom, Trezor, Ledger, Coinbase, Binance, Kraken, Exodus, Atomic, Trust, Gemini, Coinomi, Jaxx, Electrum, Bitcoin-Qt, Litecoin-Qt, Ethereum Wallet, MyEtherWallet, Uniswap, PancakeSwap, OpenSea, NFT apps, DeFi apps

### 2. Sensitive Keyword Detection

**How it works:**
- Monitors window titles for sensitive keywords
- Automatically pauses word counting when sensitive terms are detected
- Customizable list of keywords

**Default Sensitive Keywords:**
- password, login, sign in, authentication, security
- credit card, ssn, social security, bank, account
- private, confidential, secret, secure
- wallet, crypto, bitcoin, ethereum, blockchain, defi, nft
- private key, seed phrase, mnemonic, recovery, backup
- metamask, phantom, trezor, ledger, coinbase, binance
- exchange, trading, portfolio, balance, transaction
- swap, stake, yield, liquidity, token, coin

### 3. Real-time Context Awareness

**How it works:**
- Continuously monitors active window and application
- Updates security status in real-time
- Provides visual feedback about current security context

## How to Use Security Features

### Accessing Security Settings

1. Launch the Word Counter application
2. Go to **Tools** → **Security Settings**
3. Configure your security preferences

### Security Settings Dialog

The Security Settings dialog provides:

1. **Enable/Disable Security Features**
   - Toggle security features on/off globally

2. **Excluded Applications Management**
   - View current excluded applications
   - Add new applications to exclude
   - Remove applications from exclusion list

3. **Sensitive Keywords Management**
   - Edit the list of sensitive keywords
   - Add custom keywords for your specific needs

4. **Current Context Display**
   - See which application is currently active
   - View current window title
   - Check if current context is considered sensitive

### Adding Custom Exclusions

1. Open Security Settings
2. Click "Add Application" in the Excluded Applications section
3. Enter the application name (e.g., "myapp.exe")
4. The application will be excluded from word counting

### Customizing Sensitive Keywords

1. Open Security Settings
2. Edit the text in the "Sensitive Keywords" section
3. Add keywords separated by commas
4. Click "Save" to apply changes

## Security Best Practices

### 1. Keep Security Features Enabled
- Always keep security features enabled unless you have a specific reason to disable them
- The application is designed to work seamlessly with security features active

### 2. Regularly Review Excluded Applications
- Periodically check your excluded applications list
- Add any new applications you use for sensitive data
- Remove applications that no longer need exclusion

### 3. Customize Keywords for Your Environment
- Add keywords specific to your work or personal environment
- Consider terms used in your industry or organization
- Include variations of sensitive terms

### 4. Test Security Features
- Use the "Update Context" button in Security Settings to verify detection
- Test with different applications to ensure proper exclusion
- Verify that sensitive windows are properly detected

## Technical Implementation

### Dependencies Required

The security features require these additional Python packages:
```
psutil>=5.8.0    # Process and system monitoring
pywin32>=300     # Windows API access for window detection
```

### Installation

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### How Detection Works

1. **Process Detection**: Uses `psutil` to identify the active process
2. **Window Detection**: Uses `win32gui` to get window titles and process IDs
3. **Context Analysis**: Combines process and window information to determine sensitivity
4. **Real-time Monitoring**: Continuously updates context during recording sessions

## Privacy Assurance

### What is NOT Logged
- Keystrokes in excluded applications
- Keystrokes in windows with sensitive keywords
- Any data when security features are active

### What is Logged
- Only word count statistics (numbers, not actual words)
- Session duration and timing
- Productivity metrics
- No actual text content is ever stored

### Data Storage
- All data is stored locally on your computer
- No data is transmitted to external servers
- Export files contain only aggregated statistics

## Troubleshooting

### Security Features Not Working
1. Ensure required dependencies are installed
2. Check that security features are enabled in settings
3. Verify the application has necessary permissions
4. Test with the "Update Context" feature

### False Positives
- If legitimate applications are being excluded, remove them from the exclusion list
- If window titles contain false positive keywords, customize the keyword list

### Performance Impact
- Security features have minimal performance impact
- Context detection occurs only when needed
- No continuous background monitoring when not recording

## Future Enhancements

Potential future security improvements:
- Machine learning-based sensitive content detection
- Integration with Windows Credential Manager
- Advanced pattern recognition for sensitive data
- Cross-platform security features (macOS, Linux)

## Support

If you encounter issues with security features:
1. Check the application logs for error messages
2. Verify all dependencies are properly installed
3. Test with the built-in context detection tools
4. Review the security settings configuration

---

**Note**: These security features are designed to provide reasonable protection against accidental logging of sensitive data. However, no security system is perfect, and users should always exercise caution when entering sensitive information while any monitoring software is running. 