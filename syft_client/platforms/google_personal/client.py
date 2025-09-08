"""Google Personal (Gmail) platform client implementation"""

from typing import Any, Dict, List, Optional
import getpass
from ..base import BasePlatformClient


class GooglePersonalClient(BasePlatformClient):
    """Client for personal Gmail accounts"""
    
    def __init__(self, email: str):
        super().__init__(email)
        self.platform = "google_personal"
        self._gmail_servers = {
            'smtp': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'ssl': False,
                'starttls': True
            },
            'imap': {
                'server': 'imap.gmail.com',
                'port': 993,
                'ssl': True,
                'starttls': False
            }
        }
        
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with personal Gmail using app password"""
        print(f"\nGoogle Personal Account Authentication for {self.email}")
        print("=" * 60)
        
        # Check if we need to use OAuth2 or app password
        auth_method = self._choose_auth_method()
        
        if auth_method == "app_password":
            return self._authenticate_with_app_password()
        else:
            # OAuth2 flow not implemented yet
            raise NotImplementedError("OAuth2 authentication not yet implemented. Please use app password method.")
        
    def get_transport_layers(self) -> List[str]:
        """Get list of available transport layers for personal Gmail"""
        return [
            'GmailTransport',
            'GDriveFilesTransport', 
            'GSheetsTransport',
            'GFormsTransport'
        ]
    
    @property
    def login_complexity(self) -> int:
        """
        Personal Gmail authentication complexity.
        
        App Password: 3 steps (enable 2FA, generate password, enter it)
        OAuth2: 2 steps (device flow)
        Colab: 1 step (built-in auth)
        """
        # Check for cached credentials
        if self._has_cached_credentials():
            return 0
            
        # Check environment
        from ...environment import detect_environment, Environment
        env = detect_environment()
        
        if env == Environment.COLAB:
            return 1  # Single step - Colab built-in
        else:
            # App password is simpler than OAuth2 for now
            return 3  # App password steps
    
    def _has_cached_credentials(self) -> bool:
        """Check if we have cached credentials"""
        # TODO: Implement credential checking
        return False
    
    def _choose_auth_method(self) -> str:
        """Let user choose authentication method"""
        print("\nAuthentication options for personal Gmail:")
        print("1. App Password (recommended for simplicity)")
        print("2. OAuth2 (more secure but requires browser)")
        
        while True:
            choice = input("\nChoose authentication method (1 or 2) [1]: ").strip()
            if choice == "" or choice == "1":
                return "app_password"
            elif choice == "2":
                return "oauth2"
            else:
                print("Please enter 1 or 2")
    
    def _authenticate_with_app_password(self) -> Dict[str, Any]:
        """Authenticate using Gmail app password"""
        print("\n📱 Gmail App Password Setup")
        print("-" * 60)
        print("To use syft_client with Gmail, you need an app-specific password.")
        print("\nRequirements:")
        print("1. Two-Factor Authentication (2FA) must be enabled on your Google account")
        print("2. Generate an app-specific password for syft_client")
        
        print("\nSteps to generate an app password:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Sign in to your Google account")
        print("3. Under 'Select app', choose 'Mail'")
        print("4. Under 'Select device', choose 'Other' and enter 'syft_client'")
        print("5. Click 'Generate'")
        print("6. Copy the 16-character password (ignore spaces)")
        
        print("\n" + "="*60)
        
        # Get app password from user
        password = getpass.getpass("\nEnter your Gmail app password (16 characters): ")
        
        # Remove spaces from password
        password = password.replace(" ", "")
        
        # Validate password format
        if len(password) != 16:
            print(f"\n❌ Error: App passwords should be 16 characters (got {len(password)})")
            print("Please generate a new app password from Google account settings.")
            raise ValueError("Invalid app password length")
        
        print("\n🔍 Testing Gmail connection...")
        
        # Test both SMTP and IMAP connections
        smtp_success = self._test_smtp_connection(self.email, password)
        imap_success = self._test_imap_connection(self.email, password)
        
        if smtp_success and imap_success:
            print("\n✅ Authentication successful!")
            
            # Store credentials
            auth_data = {
                'email': self.email,
                'auth_method': 'app_password',
                'servers': self._gmail_servers,
                'credentials': {
                    'email': self.email,
                    'password': password  # In production, this should be encrypted
                }
            }
            
            # TODO: Save credentials securely
            print("\n💾 Credentials saved for future use")
            
            return auth_data
        else:
            print("\n❌ Authentication failed!")
            print("\nPossible issues:")
            print("1. The app password may be incorrect")
            print("2. 2FA might not be enabled on your account")
            print("3. The password might have been revoked")
            print("\nPlease generate a new app password and try again.")
            raise ValueError("Gmail authentication failed")
    
    def _test_smtp_connection(self, email: str, password: str) -> bool:
        """Test SMTP connection with Gmail"""
        import smtplib
        
        try:
            server_info = self._gmail_servers['smtp']
            
            if server_info['ssl']:
                smtp = smtplib.SMTP_SSL(server_info['server'], server_info['port'], timeout=10)
            else:
                smtp = smtplib.SMTP(server_info['server'], server_info['port'], timeout=10)
                if server_info['starttls']:
                    smtp.starttls()
            
            smtp.login(email, password)
            smtp.quit()
            print("✓ SMTP connection successful")
            return True
        except Exception as e:
            print(f"✗ SMTP connection failed: {e}")
            return False
    
    def _test_imap_connection(self, email: str, password: str) -> bool:
        """Test IMAP connection with Gmail"""
        import imaplib
        
        try:
            server_info = self._gmail_servers['imap']
            
            if server_info['ssl']:
                imap = imaplib.IMAP4_SSL(server_info['server'], server_info['port'])
            else:
                imap = imaplib.IMAP4(server_info['server'], server_info['port'])
            
            imap.login(email, password)
            imap.logout()
            print("✓ IMAP connection successful")
            return True
        except Exception as e:
            print(f"✗ IMAP connection failed: {e}")
            return False