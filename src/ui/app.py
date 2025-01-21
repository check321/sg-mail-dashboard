import gradio as gr
from services.email_service import EmailService

def create_app():
    email_service = EmailService()
    
    def list_addresses():
        """
        获取邮件列表，并在最后一列直接存储该邮箱的ID，用于删除操作
        """
        addresses = email_service.list_email_addresses()
        for row in addresses:
            if len(row) >= 1:
                # 给最后一列写入 "图标+ID" 的格式
                # 例如 原来 row = [123, "test@example.com", ...]
                # 加入后 row = [123, "test@example.com", ..., "🗑️|123"]
                record_id = row[0]
                row.append(f"🗑️|{record_id}")
        return addresses
    
    def generate_password():
        """生成6位随机密码"""
        return email_service.generate_simple_password()
    
    def delete_address(evt: gr.SelectData):
        """删除邮件地址（仅基于ID，不使用行索引）"""
        try:
            # 获取点击的列索引
            col_index = evt.index[1]  # （evt.index[0] 为行索引，这里不再使用）
            
            if col_index == 6:  # 点击最后一列（索引从0开始）
                # evt.value 形如 "🗑️|123"
                cell_data = str(evt.value)
                if "|" not in cell_data:
                    raise Exception("无法解析ID：单元格中无"|"分隔符")
                email_id = cell_data.split("|", 1)[1]  # 去掉"��️|"
                print(f"解析到的邮件ID: {email_id}")
                
                result = email_service.delete_email_address(email_id)
                if "成功" in result:
                    # 删除成功后刷新列表
                    updated_list = list_addresses()
                    return result, updated_list
                return result, None
            
            # 如果不是最后一列，则不触发删除
            return None, None
        
        except Exception as e:
            print(f"删除操作出错: {str(e)}")
            print(f"事件数据: index={evt.index}, value={evt.value}")
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