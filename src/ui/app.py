import gradio as gr
from services.email_service import EmailService
import json
import os

def create_app():
    # 加载认证信息
    def load_auth():
        auth_path = os.path.join('config', 'auth.json')
        try:
            with open(auth_path, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
                return auth_data.get('ui_auth', {})
        except Exception as e:
            print(f"加载认证配置失败: {str(e)}")
            return {}
    
    # 获取认证信息
    ui_auth = load_auth()
    email_service = EmailService()
    
    def list_addresses():
        """获取邮件列表，并添加删除按钮"""
        addresses = email_service.list_email_addresses()
        # 为每行添加删除按钮
        for row in addresses:
            if len(row) >= 1:  # 确保行数据有效
                row.append("🗑️")  # 使用删除图标
        return addresses
    
    def generate_password():
        """生成6位随机密码"""
        return email_service.generate_simple_password()
    
    def delete_address(evt: gr.SelectData):
        """删除邮件地址"""
        try:
            # 获取点击的行和列索引
            row_index = evt.index[0]    # 行索引
            col_index = evt.index[1]    # 列索引
            
            if col_index == 6:  # 点击删除按钮列（索引从0开始）
                # 从当前数据表中获取完整的行数据
                current_data = email_list.value
                if not current_data or row_index >= len(current_data):
                    raise Exception("无法获取行数据")
                
                row_data = current_data[row_index]
                if not row_data or len(row_data) < 1:
                    raise Exception("行数据无效")
                
                email_id = str(row_data[0])  # 获取ID（第一列）
                if not email_id.isdigit():
                    raise Exception(f"无效的邮件ID: {email_id}")
                
                print(f"正在删除邮件ID: {email_id}")
                print(f"完整行数据: {row_data}")
                
                result = email_service.delete_email_address(email_id)
                if "成功" in result:
                    # 删除成功后刷新列表
                    updated_list = list_addresses()
                    return result, updated_list
                return result, None
            return None, None  # 点击其他列不触发删除
        except Exception as e:
            print(f"删除操作出错: {str(e)}")
            print(f"事件数据: index={evt.index}, value={evt.value}")
            if hasattr(email_list, 'value'):
                print(f"当前表格数据: {email_list.value}")
            return f"删除操作出错: {str(e)}", None
    
    def add_address(username, password):
        if not username or not password:
            return "用户名和密码不能为空"
        
        if not (1 <= len(username) <= 16):
            return "用户名长度必须在1-16个字符之间"
            
        if not (6 <= len(password) <= 20):
            return "密码长度必须在6-20个字符之间"
        
        result = email_service.add_email_address(username, password)
        if "成功" in result:
            return result, list_addresses()
        return result, None
    
    # 准备认证信息
    auth_creds = None
    if ui_auth.get('username') and ui_auth.get('password'):
        print("启用身份验证...")
        auth_creds = (ui_auth['username'], ui_auth['password'])
    
    demo = gr.Blocks(
        title="邮件地址管理面板",
        css="""
            .refresh-btn { margin: 0 !important; }
            .list-header { display: flex; justify-content: space-between; align-items: center; }
            .mail-settings { 
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                border: 1px solid #e0e0e0;
            }
            .mail-settings code {
                background: #e0e0e0;
                padding: 2px 5px;
                border-radius: 3px;
            }
        """
    )
    
    if auth_creds:
        demo.auth = auth_creds
    
    with demo:
        with gr.Row():
            with gr.Column():
                gr.Markdown("# 邮件地址管理系统")
        
        with gr.Tabs() as tabs:
            # 邮件列表标签页
            with gr.Tab("邮件列表"):
                with gr.Column():
                    # 列表头部区域
                    with gr.Row(elem_classes="list-header"):
                        gr.Column(scale=3)  # 左侧空白
                        with gr.Column(scale=1):
                            refresh_btn = gr.Button(
                                "🔄 刷新",
                                elem_classes="refresh-btn",
                                size="sm"
                            )
                    
                    email_list = gr.Dataframe(
                        headers=[
                            "ID", 
                            "邮件地址", 
                            "用户名", 
                            "邮件数量",
                            "已用空间",
                            "状态",
                            "操作"
                        ],
                        label="邮件地址列表",
                        interactive=False
                    )
                    list_result_text = gr.Textbox(
                        label="操作结果",
                        interactive=False,
                        visible=True
                    )
            
            # 新建邮箱标签页
            with gr.Tab("新建邮箱"):
                with gr.Column():
                    # 添加邮箱设置提示
                    with gr.Column(elem_classes="mail-settings"):
                        gr.Markdown("""
                            ### 邮箱服务器设置
                            
                            **收件设置**
                            - 服务器: `mail.yszw-shoji.co.jp`
                            - IMAP端口: `993`
                            
                            **发件设置**
                            - 服务器: `mail.yszw-shoji.co.jp`
                            - SMTP端口: `465`
                        """)
                    
                    # 用户名输入行
                    with gr.Row():
                        username_input = gr.Textbox(
                            label="用户名",
                            placeholder="输入1-16个字符",
                            scale=3,
                            container=False
                        )
                        gr.Textbox(
                            value="@yszw-shoji.co.jp",
                            interactive=False,
                            container=False,
                            scale=2
                        )
                    
                    # 密码输入行
                    with gr.Row():
                        password_input = gr.Textbox(
                            label="密码",
                            placeholder="输入6-20个字符",
                            scale=3,
                            container=False
                        )
                        with gr.Column(scale=2, min_width=150):
                            generate_btn = gr.Button(
                                "生成密码",
                                scale=1
                            )
                    
                    # 创建按钮
                    with gr.Row():
                        add_btn = gr.Button(
                            "创建邮箱",
                            variant="primary",
                            scale=1
                        )
                    
                    # 新建邮箱的操作结果
                    add_result_text = gr.Textbox(
                        label="操作结果",
                        interactive=False,
                        visible=True
                    )
        
        # 事件处理
        generate_btn.click(
            fn=generate_password,
            outputs=password_input
        )
        
        add_btn.click(
            fn=add_address,
            inputs=[username_input, password_input],
            outputs=[add_result_text, email_list]
        )
        
        refresh_btn.click(
            fn=list_addresses,
            outputs=email_list
        )
        
        email_list.select(
            fn=delete_address,
            outputs=[list_result_text, email_list]
        )
        
        # 页面加载时自动获取列表
        demo.load(
            fn=list_addresses,
            outputs=email_list
        )
    
    return demo 