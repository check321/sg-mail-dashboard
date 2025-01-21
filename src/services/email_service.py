import requests
from typing import List, Dict, Optional
import yaml
import json
import os

class EmailService:
    def __init__(self):
        self.config = self._load_config()
        self.auth = self._load_auth()
        self.base_url = "https://gsgp5.siteground.asia/api-sgcp/v00"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.auth['api_token']}",
            'User-Agent':"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        config_path = os.path.join('config', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_auth(self) -> dict:
        """加载认证信息"""
        auth_path = os.path.join('config', 'auth.json')
        try:
            with open(auth_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("认证配置文件不存在，请确保 config/auth.json 文件存在")
        except json.JSONDecodeError:
            raise Exception("认证配置文件格式错误，请确保是有效的JSON格式")
    
    def update_token(self, new_token: str) -> bool:
        """更新API令牌"""
        try:
            auth_path = os.path.join('config', 'auth.json')
            auth_data = {'api_token': new_token}
            
            # 保存新的令牌
            with open(auth_path, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=4)
            
            # 更新当前实例的认证信息
            self.auth['api_token'] = new_token
            self.headers['Authorization'] = f"Bearer {new_token}"
            
            return True
        except Exception as e:
            print(f"更新令牌失败: {str(e)}")
            return False
    
    def refresh_token(self) -> bool:
        """刷新API令牌"""
        try:
            # 设置通用请求头
            common_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://my.siteground.com',
                'Referer': 'https://my.siteground.com/'
            }
            
            # 第一步：获取client_token
            refresh_token = self.auth.get('refresh_token')
            if not refresh_token:
                raise Exception("刷新令牌不存在")
            
            print(f"开始第一步: 获取client_token...")
            response = requests.post(
                "https://client-token.siteground.com/v1/auth/client-token",
                json={"refresh_token": refresh_token},
                headers=common_headers
            )
            
            print(f"第一步响应状态码: {response.status_code}")
            print(f"第一步响应内容: {response.text}")
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                print(f"解析响应JSON失败: {str(e)}")
                print(f"原始响应内容: {response.text}")
                raise Exception("解析响应JSON失败")
            
            if response_data['status'] != 200:
                raise Exception(f"获取client_token失败: {response_data.get('message')}")
            
            client_token = response_data['data']['client_token']
            print("成功获取client_token")
            
            # 第二步：获取site_token
            print(f"开始第二步: 获取site_token...")
            response = requests.get(
                "https://st.siteground.com/v1/auth/sites/S0EzeVpuNEpJUT09/token",
                params={"_client_token": client_token},
                headers=common_headers
            )
            
            print(f"第二步响应状态码: {response.status_code}")
            print(f"第二步响应内容: {response.text}")
            
            try:
                response_data = response.json()
            except json.JSONDecodeError as e:
                print(f"解析响应JSON失败: {str(e)}")
                print(f"原始响应内容: {response.text}")
                raise Exception("解析响应JSON失败")
            
            if response_data['status'] != 200:
                raise Exception(f"获取site_token失败: {response_data.get('message')}")
            
            site_token = response_data['data']['site_token']
            print("成功获取site_token")
            
            # 更新auth.json文件
            print("开始更新本地配置...")
            self.auth['api_token'] = site_token
            auth_path = os.path.join('config', 'auth.json')
            with open(auth_path, 'w', encoding='utf-8') as f:
                json.dump(self.auth, f, indent=4)
            
            # 更新当前实例的headers
            self.headers['Authorization'] = f"Bearer {site_token}"
            
            print("令牌刷新成功")
            return True
            
        except Exception as e:
            print(f"刷新令牌失败，详细错误: {str(e)}")
            print(f"错误类型: {type(e).__name__}")
            if hasattr(e, '__traceback__'):
                import traceback
                print(f"错误堆栈:\n{''.join(traceback.format_tb(e.__traceback__))}")
            return False
    
    def _check_token_expired(self, response_data: dict) -> bool:
        """检查令牌是否过期或无效"""
        message = str(response_data.get('message', '')).lower()
        status = response_data.get('status')
        
        # 检查所有可能的令牌无效情况
        token_invalid_cases = [
            # 令牌过期
            (status == 403 and 'token is expired' in message),
            # 未授权
            (status == 401 and 'no authorization' in message),
            # 无法验证令牌
            (status == 401 and 'can not verify token' in message),
            # 其他401错误
            (status == 401)
        ]
        
        # 如果满足任一条件，则认为令牌需要刷新
        if any(token_invalid_cases):
            print(f"令牌验证失败: {response_data.get('message')} (状态码: {status})")
            return True
        
        return False
    
    def list_email_addresses(self) -> List[List]:
        """获取邮件地址列表"""
        try:
            response = requests.get(
                f"{self.base_url}/email",
                headers=self.headers
            )
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print(f"API响应解析失败: {response.text}")
                return []
            
            # 检查令牌是否过期或无效，如果是则尝试刷新
            if self._check_token_expired(response_data):
                print("尝试刷新令牌...")
                if self.refresh_token():
                    # 刷新成功后重试请求
                    return self.list_email_addresses()
                else:
                    raise Exception("令牌刷新失败")
            
            if response_data['status'] != 200:
                raise Exception(f"API错误: {response_data.get('message', '未知错误')}")
            
            # 转换为表格显示格式
            return [[
                email['id'],
                f"{email['name']}@{email['domain_name']}", # 完整邮件地址
                email['name'],                             # 用户名
                email.get('n_emails', 0),                  # 邮件数量
                self._format_size(email.get('used_size', 0)), # 已使用空间
                '已停用' if email['suspended'] else '正常'    # 状态
            ] for email in response_data['data']]
            
        except Exception as e:
            print(f"获取邮件列表失败: {str(e)}")
            return []
    
    def _format_size(self, size_in_bytes: int) -> str:
        """将字节转换为可读格式"""
        if not size_in_bytes:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} TB"
    
    def generate_simple_password(self) -> str:
        """生成简单的6位随机密码（字母数字组合）"""
        import random
        import string
        
        # 定义字符集
        chars = string.ascii_letters + string.digits  # 大小写字母 + 数字
        
        # 生成6位随机密码
        password = ''.join(random.choice(chars) for _ in range(6))
        
        return password
    
    def add_email_address(self, username: str, password: str) -> str:
        """添加新的邮件地址"""
        try:
            # 准备请求数据
            data = {
                'name': username.strip(),
                'password': password,
                'domain_id': 1
            }
            
            response = requests.post(
                f"{self.base_url}/email",
                headers=self.headers,
                json=data
            )
            
            response_data = response.json()
            
            # 检查令牌是否过期或无效
            if self._check_token_expired(response_data):
                print("令牌已过期或无效，尝试刷新...")
                if self.refresh_token():
                    # 刷新成功后重试请求
                    return self.add_email_address(username, password)
                else:
                    raise Exception("令牌刷新失败")
            
            if response_data['status'] != 200:
                raise Exception(f"API错误: {response_data.get('message', '未知错误')}")
            
            # 返回成功信息，包含创建的邮件地址
            created_email = f"{response_data['data']['name']}@{response_data['data']['domain_name']}"
            return f"邮件地址创建成功\n邮箱: {created_email}"
            
        except Exception as e:
            print(f"添加邮件地址失败: {str(e)}")
            return f"添加失败：{str(e)}"
    
    def delete_email_address(self, email_id: str) -> str:
        """删除邮件地址"""
        try:
            response = requests.delete(
                f"{self.base_url}/email/{email_id}",
                headers=self.headers
            )
            
            response_data = response.json()
            
            # 检查令牌是否过期或无效
            if self._check_token_expired(response_data):
                print("令牌已过期或无效，尝试刷新...")
                if self.refresh_token():
                    # 刷新成功后重试请求
                    return self.delete_email_address(email_id)
                else:
                    raise Exception("令牌刷新失败")
            
            if response_data['status'] != 200:
                raise Exception(f"API错误: {response_data.get('message', '未知错误')}")
            
            return "邮件地址删除成功"
        except Exception as e:
            print(f"删除邮件地址失败: {str(e)}")
            return f"删除失败：{str(e)}" 