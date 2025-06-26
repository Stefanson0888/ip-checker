# affiliate_config.py
# NordVPN Real Affiliate Configuration

# NordVPN Affiliate Details (from Tomas email)
NORDVPN_AFFILIATE_CONFIG = {
    "affiliate_id": "126137",
    "account_manager": "Tomas",
    "
    # NordVPN Main Product
    "nordvpn": {
        "offer_id": "15",
        "url_id": "902", 
        "base_url": "https://go.nordvpn.net/aff_c",
        "full_url": "https://go.nordvpn.net/aff_c?offer_id=15&aff_id=126137&url_id=902"
    },
    
    # NordPass Password Manager
    "nordpass": {
        "offer_id": "488",
        "url_id": "9356",
        "base_url": "https://go.nordpass.io/aff_c", 
        "full_url": "https://go.nordpass.io/aff_c?offer_id=488&aff_id=126137&url_id=9356"
    }
}

# Function to generate tracking URLs with custom parameters
def get_nordvpn_url(source_page="checkip", campaign="vpn_detection"):
    """Generate NordVPN affiliate URL with tracking parameters"""
    base_url = NORDVPN_AFFILIATE_CONFIG["nordvpn"]["full_url"]
    tracking_params = f"&source={source_page}&campaign={campaign}"
    return base_url + tracking_params

def get_nordpass_url(source_page="checkip", campaign="password_security"):
    """Generate NordPass affiliate URL with tracking parameters"""
    base_url = NORDVPN_AFFILIATE_CONFIG["nordpass"]["full_url"] 
    tracking_params = f"&source={source_page}&campaign={campaign}"
    return base_url + tracking_params

# Export URLs for templates
AFFILIATE_URLS = {
    "nordvpn_main": get_nordvpn_url("vpn_detection", "main_cta"),
    "nordvpn_secondary": get_nordvpn_url("vpn_detection", "secondary_cta"),
    "nordpass_main": get_nordpass_url("vpn_detection", "password_manager"),
    
    # For different pages (future use)
    "nordvpn_homepage": get_nordvpn_url("homepage", "hero_banner"),
    "nordvpn_whatismyip": get_nordvpn_url("what_is_my_ip", "sidebar_cta")
}