import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import re


class ArticleScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文章爬取工具")
        self.root.geometry("550x400")
        self.root.resizable(False, False)

        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')

        # 主框架
        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL输入区域
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(url_frame, text="文章链接:", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("微软雅黑", 9))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 状态标签
        self.status_var = tk.StringVar(value="等待输入URL...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("微软雅黑", 9), foreground="gray")
        status_label.pack(anchor=tk.W, pady=(0, 10))

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=(0, 10))

        # 预览区域标签
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(preview_frame, text="📄 内容预览", font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)

        # 保存按钮
        self.save_btn = ttk.Button(preview_frame, text="💾 保存文件", command=self.save_article, state=tk.DISABLED,
                                   width=12)
        self.save_btn.pack(side=tk.RIGHT)

        # 结果显示区域
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # 文本框
        self.result_text = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 9),
                                   bg="#f8f8f8", fg="#333333", relief=tk.FLAT,
                                   borderwidth=0, highlightthickness=1, highlightcolor="#d3d3d3")
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        # 绑定事件
        self.url_var.trace_add('write', self.on_url_change)
        self.url_entry.bind('<Return>', lambda e: self.start_scraping())

        # 存储数据
        self.save_path = None
        self.current_title = None
        self.current_content = None

    def on_url_change(self, *args):
        """URL变化时更新状态"""
        url = self.url_var.get().strip()
        if url:
            self.status_var.set("✅ URL已就绪，按回车键开始爬取")
            self.status_var.config(foreground="green")
        else:
            self.status_var.set("等待输入URL...")
            self.status_var.config(foreground="gray")

    def clean_text(self, text):
        """美化文本"""
        # 替换多个换行为单个空行
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # 去除每行首尾空格
        lines = [line.strip() for line in text.splitlines()]
        # 移除空行
        lines = [line for line in lines if line]
        return '\n\n'.join(lines)

    def save_to_txt(self, title, content):
        """保存为 TXT 文件"""
        # 清理文件名
        title_clean = re.sub(r'[<>:"/\\|?*]', '_', title)

        # 弹出保存对话框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"{title_clean}.txt"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'【标题】{title}\n\n')
                f.write(content)
            return file_path
        return None

    def scrape_article(self):
        """爬取文章"""
        url = self.url_var.get().strip()

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            # 请求网页
            self.update_status("🌐 正在请求网页...")
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                raise Exception(f'HTTP {response.status_code}')

            self.update_status("🔍 正在解析内容...")
            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取标题
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else '未命名文章'

            # 提取正文
            content_div = soup.find('div', class_='article-content')
            if content_div:
                p_tags = content_div.find_all('p')
            else:
                p_tags = soup.find_all('p')

            # 处理段落
            paragraphs = []
            for p in p_tags:
                text = p.get_text().strip()
                if text:
                    paragraphs.append(text)

            article_text = '\n\n'.join(paragraphs)
            final_text = self.clean_text(article_text)

            # 显示预览
            self.show_preview(title, final_text)

            # 保存内容
            self.current_title = title
            self.current_content = final_text

            self.update_status(f"✅ 爬取成功！标题：{title[:30]}{'...' if len(title) > 30 else ''}")
            return True

        except requests.exceptions.RequestException as e:
            self.update_status(f"❌ 网络错误：{str(e)[:50]}")
            return False
        except Exception as e:
            self.update_status(f"❌ 解析错误：{str(e)[:50]}")
            return False

    def show_preview(self, title, content):
        """显示预览"""
        self.result_text.delete(1.0, tk.END)

        # 插入标题
        self.result_text.insert(1.0, f"【{title}】\n\n", "title")
        self.result_text.tag_configure("title", font=("微软雅黑", 10, "bold"), foreground="#0066cc")

        # 插入内容预览（前800字符）
        preview = content[:800]
        if len(content) > 800:
            preview += "\n\n...(内容过长，仅显示前800字符)"

        self.result_text.insert(tk.END, preview)
        self.result_text.configure(state=tk.NORMAL)

    def save_article(self):
        """保存文章"""
        if not self.current_content:
            messagebox.showwarning("警告", "没有可保存的内容")
            return

        try:
            filepath = self.save_to_txt(self.current_title, self.current_content)
            if filepath:
                self.update_status(f"💾 已保存：{os.path.basename(filepath)}")
                messagebox.showinfo("成功", f"文章已保存到：\n{filepath}")
                self.save_btn.config(state=tk.DISABLED)
            else:
                self.update_status("保存已取消")
        except Exception as e:
            self.update_status(f"❌ 保存失败：{str(e)[:50]}")
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def start_scraping(self):
        """开始爬取"""
        if not self.url_var.get().strip():
            messagebox.showwarning("提示", "请输入文章链接")
            return

        # 禁用输入和按钮
        self.url_entry.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.progress.start()

        # 清空预览
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, "正在爬取中，请稍候...")

        # 新线程执行
        thread = threading.Thread(target=self.scraping_thread)
        thread.daemon = True
        thread.start()

    def scraping_thread(self):
        """爬取线程"""
        success = self.scrape_article()

        # 恢复界面
        self.root.after(0, lambda: self.finish_scraping(success))

    def finish_scraping(self, success):
        """完成爬取"""
        self.progress.stop()
        self.url_entry.config(state=tk.NORMAL)

        if success:
            self.save_btn.config(state=tk.NORMAL)
        else:
            self.save_btn.config(state=tk.DISABLED)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, "爬取失败，请检查链接是否正确")

    def update_status(self, message):
        """更新状态"""
        self.root.after(0, lambda: self.status_var.set(message))


def main():
    root = tk.Tk()
    app = ArticleScraperApp(root)

    # 居中显示
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()