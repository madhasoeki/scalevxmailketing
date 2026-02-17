import requests

class MailketingService:
    """Service for interacting with Mailketing API"""
    
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = 'https://api.mailketing.co.id/api/v1'
    
    def get_all_lists(self):
        """Get all lists from Mailketing account"""
        # Endpoint: POST https://api.mailketing.co.id/api/v1/viewlist
        try:
            response = requests.post(
                f'{self.base_url}/viewlist',
                data={'api_token': self.api_token},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"Mailketing API Response: {data.get('status')}")
            
            # Response format: {"status":"success","lists":[{"list_id":123,"list_name":"Name"},...]}
            if isinstance(data, dict) and data.get('status') == 'success':
                lists = data.get('lists', [])
                print(f"  Lists returned: {len(lists)}")
                return lists
            elif isinstance(data, dict) and data.get('status') == 'error':
                error_msg = data.get('message', 'Unknown error')
                print(f"  Mailketing API Error: {error_msg}")
                raise Exception(f"Mailketing API Error: {error_msg}")
            
            print(f"  Unexpected response format: {data}")
            return []
        except requests.exceptions.RequestException as e:
            print(f"  Network error: {str(e)}")
            raise Exception(f"Network error connecting to Mailketing: {str(e)}")
        except Exception as e:
            print(f"  Error in get_all_lists: {str(e)}")
            raise
    
    def add_subscriber(self, list_id, email, first_name=None, last_name=None, 
                       city=None, state=None, country=None, company=None, 
                       phone=None, mobile=None):
        """Add subscriber to a list
        
        Args:
            list_id: List ID dari Mailketing
            email: Email subscriber
            first_name: Nama depan
            last_name: Nama belakang
            city: Kota
            state: Provinsi
            country: Negara
            company: Nama perusahaan
            phone: Nomor kantor
            mobile: Nomor handphone
        """
        # Endpoint: POST https://api.mailketing.co.id/api/v1/addsubtolist
        payload = {
            'api_token': self.api_token,
            'list_id': str(list_id),
            'email': email
        }
        
        # Add optional parameters if provided
        if first_name:
            payload['first_name'] = first_name
        if last_name:
            payload['last_name'] = last_name
        if city:
            payload['city'] = city
        if state:
            payload['state'] = state
        if country:
            payload['country'] = country
        if company:
            payload['company'] = company
        if phone:
            payload['phone'] = phone
        if mobile:
            payload['mobile'] = mobile
        
        response = requests.post(
            f'{self.base_url}/addsubtolist',
            data=payload
        )
        response.raise_for_status()
        result = response.json()
        
        return result
    
    def get_list_details(self, list_id):
        """Get details of a specific list"""
        response = requests.post(
            f'{self.base_url}/viewlist',
            data={
                'api_token': self.api_token,
                'list_id': list_id
            }
        )
        response.raise_for_status()
        return response.json()
