# Security Solutions for Password/Keyphrase Protection

## Problem Addressed

You raised a valid security concern: the word counter application could accidentally log passwords or sensitive keyphrases, which could be exploited if the data were compromised.

## Solutions Implemented

### 🛡️ **Primary Solution: Application Exclusion List**

**What it does:**
- Automatically detects when you're using applications that typically contain sensitive data
- Completely stops word counting when these applications are active
- No keystrokes are processed or logged in excluded applications

**Default Protected Applications:**
- **Browsers** (Chrome, Firefox, Edge, Safari, Brave, Opera) - where passwords are often entered
- **Email Clients** (Outlook, Thunderbird) - for email passwords
- **Password Managers** (KeePass, 1Password, LastPass, Bitwarden)
- **SSH Clients** (PuTTY, MobaXterm) - for server credentials
- **Communication Apps** (Teams, Slack, Discord) - for account logins
- **Command Line** (CMD, PowerShell) - for system commands
- **VPN Clients** - for connection credentials
- **Crypto Wallets & Financial Apps** (MetaMask, Phantom, Trezor, Ledger, Coinbase, Binance, Kraken, Exodus, Atomic, Trust, Gemini, Coinomi, Jaxx, Electrum, Bitcoin-Qt, Litecoin-Qt, Ethereum Wallet, MyEtherWallet, Uniswap, PancakeSwap, OpenSea, NFT apps, DeFi apps) - for private keys and financial data

### 🔍 **Secondary Solution: Sensitive Keyword Detection**

**What it does:**
- Monitors window titles for sensitive keywords
- Automatically pauses word counting when sensitive terms are detected
- Customizable list of keywords

**Default Keywords:**
- password, login, sign in, authentication, security
- credit card, ssn, social security, bank, account
- private, confidential, secret, secure
- wallet, crypto, bitcoin, ethereum, blockchain, defi, nft
- private key, seed phrase, mnemonic, recovery, backup
- metamask, phantom, trezor, ledger, coinbase, binance
- exchange, trading, portfolio, balance, transaction
- swap, stake, yield, liquidity, token, coin

### ⚙️ **User Control: Security Settings Dialog**

**Access:** Tools → Security Settings

**Features:**
- Enable/disable security features globally
- Add/remove applications from exclusion list
- Customize sensitive keywords
- Real-time context monitoring
- Test security detection

## How It Protects You

### ✅ **What's Protected:**
- Password entry in browsers
- Login forms in any application
- Banking/financial applications
- SSH/remote access sessions
- Email client authentication
- Password manager usage
- Crypto wallet applications and browser extensions
- Private key and seed phrase entry
- Financial trading applications
- NFT and DeFi platforms
- Any window with sensitive keywords in the title

### ❌ **What's NOT Logged:**
- Keystrokes in excluded applications
- Keystrokes in sensitive windows
- Any data when security features are active
- Actual text content (only word counts are stored)

### 📊 **What IS Still Logged:**
- Word count statistics (numbers only)
- Session duration and timing
- Productivity metrics
- No actual words or text content

## Installation & Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Application:**
   ```bash
   python "wordcounter 06.28.25.py"
   ```

3. **Configure Security:**
   - Go to Tools → Security Settings
   - Review default exclusions
   - Add any custom applications you use for sensitive data
   - Customize keywords if needed

## Security Best Practices

1. **Keep Security Enabled:** Always leave security features on
2. **Review Exclusions:** Periodically check and update excluded applications
3. **Customize Keywords:** Add terms specific to your work environment
4. **Test Regularly:** Use the "Update Context" feature to verify detection

## Technical Implementation

- **Process Detection:** Uses `psutil` to identify active applications
- **Window Monitoring:** Uses `win32gui` to detect sensitive window titles
- **Real-time Analysis:** Continuously monitors context during recording
- **Zero Performance Impact:** Minimal overhead, only active during recording

## Privacy Assurance

- **Local Storage Only:** All data stays on your computer
- **No Network Transmission:** Nothing is sent to external servers
- **Aggregated Data Only:** Only statistics, never actual text content
- **User Control:** You can disable security features if needed

## Alternative Options Considered

1. **Pattern Recognition:** Could detect password-like patterns, but less reliable
2. **Manual Pause:** User manually pauses before sensitive data entry
3. **Time-based Exclusion:** Exclude certain time periods, but less precise
4. **Application Whitelist:** Only count in specific applications, but too restrictive

The implemented solution provides the best balance of security, usability, and reliability.

---

**Result:** Your word counter now automatically protects sensitive data while maintaining full functionality for legitimate writing tasks. The security features work seamlessly in the background, requiring no user intervention during normal use. 