import requests

class ScalevService:
    """Service for interacting with Scalev API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.scalev.id/v1'
        self.base_url_v2 = 'https://api.scalev.id/v2'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_products(self, limit=100):
        """Get all products using v2 API with pagination support"""
        try:
            all_products = []
            last_id = None
            has_next = True
            
            print(f"Fetching ScaleV products (max {limit})...")
            
            # Loop untuk fetch semua produk dengan pagination
            while has_next and len(all_products) < limit:
                params = {'limit': 50}
                if last_id:
                    params['last_id'] = last_id
                
                response = requests.get(
                    f'{self.base_url_v2}/products',
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                # Debug first page
                if not last_id:
                    print(f"ScaleV Response: {data.get('status')}, has_next: {data.get('data', {}).get('has_next')}")
                
                # Parse response dari v2 API
                if data.get('status') == 'Success' and 'data' in data:
                    results = data['data'].get('results', [])
                    all_products.extend(results)
                    
                    # Check jika ada halaman berikutnya
                    has_next = data['data'].get('has_next', False)
                    last_id = data['data'].get('last_id')
                    
                    print(f"Fetched {len(results)} products, total: {len(all_products)}")
                else:
                    print(f"Unexpected response format: {data}")
                    break
            
            print(f"Total products fetched: {len(all_products)}")
            return all_products[:limit]  # Batasi sesuai limit
            
        except Exception as e:
            print(f"Error fetching ScaleV products: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_order(self, order_id):
        """Get order details"""
        response = requests.get(
            f'{self.base_url}/orders/{order_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_product(self, product_id):
        """Get product details"""
        response = requests.get(
            f'{self.base_url}/products/{product_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_stores(self, limit=100):
        """Get all stores using v2 API with pagination support"""
        try:
            all_stores = []
            last_id = None
            has_next = True
            
            print(f"Fetching ScaleV stores (max {limit})...")
            
            while has_next and len(all_stores) < limit:
                params = {'page_size': 25}
                if last_id:
                    params['last_id'] = last_id
                
                response = requests.get(
                    f'{self.base_url_v2}/stores',
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'Success' and 'data' in data:
                    results = data['data'].get('results', [])
                    all_stores.extend(results)
                    
                    has_next = data['data'].get('has_next', False)
                    last_id = data['data'].get('last_id')
                    
                    print(f"Fetched {len(results)} stores, total: {len(all_stores)}")
                else:
                    break
            
            print(f"Total stores fetched: {len(all_stores)}")
            return all_stores[:limit]
            
        except Exception as e:
            print(f"Error fetching ScaleV stores: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_store_products(self, store_id, limit=100):
        """Get products from a specific store"""
        try:
            all_products = []
            last_id = None
            has_next = True
            
            print(f"Fetching products for store {store_id}...")
            
            while has_next and len(all_products) < limit:
                params = {'page_size': 25}
                if last_id:
                    params['last_id'] = last_id
                
                response = requests.get(
                    f'{self.base_url_v2}/stores/{store_id}/products',
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'Success' and 'data' in data:
                    results = data['data'].get('results', [])
                    all_products.extend(results)
                    
                    has_next = data['data'].get('has_next', False)
                    last_id = data['data'].get('last_id')
                    
                    print(f"Fetched {len(results)} products, total: {len(all_products)}")
                else:
                    break
            
            print(f"Total products fetched: {len(all_products)}")
            return all_products[:limit]
            
        except Exception as e:
            print(f"Error fetching store products: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_store_sales_people(self, store_id, limit=100):
        """Get sales people from a specific store"""
        try:
            all_sales = []
            last_id = None
            has_next = True
            
            print(f"Fetching sales people for store {store_id}...")
            
            while has_next and len(all_sales) < limit:
                params = {'page_size': 25}
                if last_id:
                    params['last_id'] = last_id
                
                response = requests.get(
                    f'{self.base_url_v2}/stores/{store_id}/sales-people',
                    headers=self.headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'Success' and 'data' in data:
                    results = data['data'].get('results', [])
                    all_sales.extend(results)
                    
                    has_next = data['data'].get('has_next', False)
                    last_id = data['data'].get('last_id')
                    
                    print(f"Fetched {len(results)} sales people, total: {len(all_sales)}")
                else:
                    break
            
            print(f"Total sales people fetched: {len(all_sales)}")
            return all_sales[:limit]
            
        except Exception as e:
            print(f"Error fetching store sales people: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
