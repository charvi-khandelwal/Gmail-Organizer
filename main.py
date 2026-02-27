#!/usr/bin/env python3
"""
Gmail Organizer - Gmail-like interface with enhanced organizing features
Features: Gmail-style UI, batch delete, sender organization, drafts, compose, send
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, font
import threading
import json
import os
import subprocess
from datetime import datetime
import sqlite3
from typing import List, Dict, Optional

# Email service imports
from gmail_service import GmailService

class GmailOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gmail Organizer")
        self.root.geometry("1200x800")

        self.theme_mode = self.detect_system_theme()
        self.palette = {}
        self.apply_palette()
        self.root.configure(bg=self.palette['bg'])
        self.root.option_add('*Cursor', 'arrow')
        self.configure_styles()
        
        # Initialize services
        self.gmail_service = GmailService()
        
        # Data storage
        self.emails = []
        self.all_emails = []
        self.email_by_id = {}
        self.selected_email_ids = set()
        self.selected_emails = []
        self.current_account = None
        self.current_folder = 'INBOX'
        self.current_category = 'PRIMARY'
        
        # Initialize database
        self.init_database()
        
        # Create Gmail-like interface
        self.create_gmail_interface()
        
        # Auto-connect if credentials available
        self.auto_connect()

    def detect_system_theme(self) -> str:
        """Detect system appearance: macOS via defaults; Windows falls back to light."""
        try:
            if os.name == "posix" and os.uname().sysname == "Darwin":
                # macOS: read system appearance
                result = subprocess.check_output(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    stderr=subprocess.DEVNULL,
                ).decode("utf-8", errors="ignore").strip()
                return "dark" if result.lower() == "dark" else "light"
            else:
                # Windows and others: default to light (could add Windows registry detection later)
                return "light"
        except Exception:
            return "light"

    def apply_palette(self):
        """Apply active color palette for current theme mode."""
        if self.theme_mode == "dark":
            self.palette = {
                'bg': '#202124',
                'surface': '#2b2d31',
                'header': '#202124',
                'text': '#e8eaed',
                'muted': '#9aa0a6',
                'selected': '#3c4043',
                'danger': '#f28b82',
                'accent': '#8ab4f8',
                'input_bg': '#3c4043',
                'input_fg': '#e8eaed',
                'button_bg': '#3c4043',
                'border': '#3c4043',
                'chip': '#3c4043',
                'row_hover': '#2f3136',
            }
        else:
            self.palette = {
                'bg': '#f6f8fc',
                'surface': '#eef2f7',
                'header': '#f6f8fc',
                'text': '#202124',
                'muted': '#5f6368',
                'selected': '#d3e3fd',
                'danger': '#d93025',
                'accent': '#1a73e8',
                'input_bg': '#ffffff',
                'input_fg': '#202124',
                'button_bg': '#ffffff',
                'border': '#dde3eb',
                'chip': '#e9eef6',
                'row_hover': '#f6f8fc',
            }

    def configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure(
            'Gmail.Treeview',
            background=self.palette['bg'],
            fieldbackground=self.palette['bg'],
            foreground=self.palette['text'],
            borderwidth=0,
            rowheight=32,
            font=('Google Sans', 10),
        )
        style.map(
            'Gmail.Treeview',
            background=[('selected', self.palette['selected'])],
            foreground=[('selected', self.palette['text'])],
        )
        style.configure(
            'Gmail.Treeview.Heading',
            background=self.palette['bg'],
            foreground=self.palette['muted'],
            relief='flat',
            borderwidth=0,
            font=('Google Sans', 9),
        )

    def enforce_default_cursor(self, widget=None):
        if widget is None:
            widget = self.root
        try:
            widget.configure(cursor='arrow')
        except Exception:
            pass
        for child in widget.winfo_children():
            self.enforce_default_cursor(child)

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        self.apply_palette()
        self.refresh_theme()

    def refresh_theme(self):
        """Repaint major widgets after theme switch."""
        self.root.configure(bg=self.palette['bg'])
        self.configure_styles()
        self.create_gmail_interface(rebuild=True)
        self.populate_email_tree()
        
    def init_database(self):
        """Initialize SQLite database for storing settings and cache"""
        self.conn = sqlite3.connect('email_organizer.db')
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                provider TEXT,
                credentials TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_email TEXT,
                message_id TEXT,
                sender TEXT,
                subject TEXT,
                date TEXT,
                snippet TEXT,
                provider TEXT,
                UNIQUE(account_email, message_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_gmail_interface(self, rebuild: bool = False):
        """Create Gmail-like interface"""
        if rebuild and hasattr(self, 'main_frame'):
            self.main_frame.destroy()

        # Main container
        main_frame = tk.Frame(self.root, bg=self.palette['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame = main_frame
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=0)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)
        
        # Create Gmail-style layout
        self.create_header(main_frame)
        self.create_sidebar(main_frame)
        self.create_email_list(main_frame)
        self.create_status_bar(main_frame)
        self.enforce_default_cursor(main_frame)
    
    def create_header(self, parent):
        """Create Gmail-style header"""
        header_frame = tk.Frame(parent, bg=self.palette['header'], height=64)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
        header_frame.grid_propagate(False)

        left = tk.Frame(header_frame, bg=self.palette['header'])
        left.pack(side=tk.LEFT, padx=10, pady=12)

        tk.Button(
            left,
            text="☰",
            font=('Google Sans', 14),
            bg=self.palette['header'],
            fg=self.palette['muted'],
            relief=tk.FLAT,
            cursor='arrow',
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            left,
            text="M",
            font=('Google Sans', 18, 'bold'),
            fg='#ea4335',
            bg=self.palette['header'],
        ).pack(side=tk.LEFT)
        tk.Label(
            left,
            text="Gmail",
            font=('Google Sans', 18),
            fg=self.palette['text'],
            bg=self.palette['header'],
        ).pack(side=tk.LEFT, padx=(6, 0))

        center = tk.Frame(header_frame, bg=self.palette['header'])
        center.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)

        search_box = tk.Frame(center, bg=self.palette['chip'], bd=0)
        search_box.pack(fill=tk.X, pady=8)

        tk.Label(
            search_box,
            text="🔍",
            font=('Google Sans', 12),
            fg=self.palette['muted'],
            bg=self.palette['chip'],
        ).pack(side=tk.LEFT, padx=10)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_box,
            textvariable=self.search_var,
            font=('Google Sans', 13),
            relief=tk.FLAT,
            bg=self.palette['chip'],
            fg=self.palette['text'],
            insertbackground=self.palette['text'],
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=8)
        self.search_entry.bind('<KeyRelease>', self.filter_emails)

        tk.Label(
            search_box,
            text="⚙",
            font=('Google Sans', 12),
            fg=self.palette['muted'],
            bg=self.palette['chip'],
        ).pack(side=tk.RIGHT, padx=10)

        right = tk.Frame(header_frame, bg=self.palette['header'])
        right.pack(side=tk.RIGHT, padx=12, pady=12)

        self.theme_btn = tk.Button(
            right,
            text="☾" if self.theme_mode == 'light' else "☀",
            command=self.toggle_theme,
            font=('Google Sans', 12),
            bg=self.palette['button_bg'],
            fg=self.palette['text'],
            activebackground=self.palette['selected'],
            activeforeground=self.palette['text'],
            relief=tk.RIDGE,
            bd=1,
            cursor='arrow',
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=4)

        self.user_label = tk.Label(
            right,
            text="Not connected",
            font=('Google Sans', 10),
            fg=self.palette['muted'],
            bg=self.palette['header'],
        )
        self.user_label.pack(side=tk.RIGHT, padx=6)
    
    def create_sidebar(self, parent):
        """Create Gmail-style sidebar"""
        rail_frame = tk.Frame(parent, bg=self.palette['surface'], width=56)
        rail_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W))
        rail_frame.grid_propagate(False)

        for label in ["Mail", "Chat", "Meet"]:
            tk.Button(
                rail_frame,
                text=label,
                font=('Google Sans', 9),
                bg=self.palette['button_bg'],
                fg=self.palette['text'],
                activebackground=self.palette['selected'],
                activeforeground=self.palette['text'],
                relief=tk.RIDGE,
                bd=1,
                cursor='arrow',
            ).pack(fill=tk.X, padx=6, pady=8)

        sidebar_frame = tk.Frame(parent, bg=self.palette['surface'], width=220)
        sidebar_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        sidebar_frame.grid_propagate(False)

        compose_frame = tk.Frame(sidebar_frame, bg=self.palette['surface'])
        compose_frame.pack(fill=tk.X, padx=10, pady=10)

        self.main_compose_btn = tk.Button(
            compose_frame,
            text="✎  Compose",
            command=self.open_compose,
            font=('Google Sans', 11, 'bold'),
            bg=self.palette['chip'],
            fg=self.palette['text'],
            activebackground=self.palette['selected'],
            activeforeground=self.palette['text'],
            relief=tk.RIDGE,
            bd=1,
            padx=14,
            pady=10,
            cursor='arrow',
        )
        self.main_compose_btn.pack(anchor=tk.W)

        folders_frame = tk.Frame(sidebar_frame, bg=self.palette['surface'])
        folders_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.folder_buttons = {}
        folders = [
            ('Inbox', 'INBOX'),
            ('Starred', 'STARRED'),
            ('Snoozed', 'SNOOZED'),
            ('Sent', 'SENT'),
            ('Drafts', 'DRAFTS'),
            ('Trash', 'TRASH'),
            ('All Mail', 'ALL'),
            ('Important', 'IMPORTANT'),
            ('Attachments', 'ATTACHMENTS'),
        ]

        for name, folder in folders:
            btn = tk.Button(
                folders_frame,
                text=name,
                command=lambda f=folder: self.switch_folder(f),
                font=('Google Sans', 10),
                bg=self.palette['button_bg'],
                fg=self.palette['text'],
                activebackground=self.palette['selected'],
                activeforeground=self.palette['text'],
                relief=tk.RIDGE,
                bd=1,
                anchor='w',
                cursor='arrow',
                padx=12,
                pady=6,
            )
            btn.pack(fill=tk.X, pady=1)
            self.folder_buttons[folder] = btn

        self.folder_buttons['INBOX'].config(bg=self.palette['selected'])

        organize_frame = tk.Frame(sidebar_frame, bg=self.palette['surface'])
        organize_frame.pack(fill=tk.X, padx=8, pady=10)

        tk.Label(
            organize_frame,
            text="Organize",
            font=('Google Sans', 10, 'bold'),
            fg=self.palette['muted'],
            bg=self.palette['surface'],
        ).pack(anchor=tk.W)

        self.select_all_btn = tk.Button(
            organize_frame,
            text="Select all",
            command=self.select_all_emails,
            font=('Google Sans', 10),
            bg=self.palette['button_bg'],
            fg=self.palette['text'],
            activebackground=self.palette['selected'],
            activeforeground=self.palette['text'],
            relief=tk.RIDGE,
            bd=1,
            anchor='w',
            cursor='arrow',
        )
        self.select_all_btn.pack(fill=tk.X)

        self.delete_selected_btn = tk.Button(
            organize_frame,
            text="Delete selected",
            command=self.delete_selected_emails,
            font=('Google Sans', 10),
            bg=self.palette['button_bg'],
            fg=self.palette['danger'],
            activebackground=self.palette['selected'],
            activeforeground=self.palette['danger'],
            relief=tk.RIDGE,
            bd=1,
            anchor='w',
            cursor='arrow',
        )
        self.delete_selected_btn.pack(fill=tk.X)

        self.clear_sender_btn = tk.Button(
            organize_frame,
            text="Clear by sender",
            command=self.clear_all_from_sender,
            font=('Google Sans', 10),
            bg=self.palette['button_bg'],
            fg=self.palette['danger'],
            activebackground=self.palette['selected'],
            activeforeground=self.palette['danger'],
            relief=tk.RIDGE,
            bd=1,
            anchor='w',
            cursor='arrow',
        )
        self.clear_sender_btn.pack(fill=tk.X)
    
    def create_email_list(self, parent):
        """Create Gmail-style email list"""
        email_list_frame = tk.Frame(parent, bg=self.palette['bg'])
        email_list_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        email_list_frame.columnconfigure(0, weight=1)
        email_list_frame.rowconfigure(0, weight=1)

        card = tk.Frame(
            email_list_frame,
            bg=self.palette['button_bg'],
            highlightbackground=self.palette['border'],
            highlightthickness=1,
        )
        card.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=8, pady=8)
        card.columnconfigure(0, weight=1)
        card.rowconfigure(3, weight=1)

        toolbar = tk.Frame(card, bg=self.palette['button_bg'], height=42)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        toolbar.grid_propagate(False)

        tk.Button(toolbar, text="☐", font=('Google Sans', 11), bg=self.palette['button_bg'], fg=self.palette['text'], relief=tk.RIDGE, bd=1, command=self.deselect_all_emails).pack(side=tk.LEFT, padx=(12, 4))
        tk.Button(toolbar, text="↻", font=('Google Sans', 11), bg=self.palette['button_bg'], fg=self.palette['text'], relief=tk.RIDGE, bd=1, command=self.refresh_gmail).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="⋮", font=('Google Sans', 11), bg=self.palette['button_bg'], fg=self.palette['text'], relief=tk.RIDGE, bd=1).pack(side=tk.LEFT, padx=4)

        self.count_label = tk.Label(
            toolbar,
            text="0 messages",
            font=('Google Sans', 9),
            fg=self.palette['muted'],
            bg=self.palette['button_bg'],
        )
        self.count_label.pack(side=tk.RIGHT, padx=12)

        banner = tk.Frame(card, bg='#f5d9d7' if self.theme_mode == 'light' else '#4a2c2a', height=78)
        banner.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=8, pady=(0, 6))
        banner.grid_propagate(False)
        tk.Label(
            banner,
            text="Out of storage\nEmails will stop on Mar 22, 2026",
            justify='left',
            font=('Google Sans', 11, 'bold'),
            fg=self.palette['text'],
            bg=banner['bg'],
        ).pack(side=tk.LEFT, padx=12, pady=8)

        tabs = tk.Frame(card, bg=self.palette['button_bg'], height=40)
        tabs.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=8)
        tabs.grid_propagate(False)

        self.category_buttons = {}
        for title, value in [("Primary", "PRIMARY"), ("Promotions", "PROMOTIONS"), ("Social", "SOCIAL")]:
            btn = tk.Button(
                tabs,
                text=title,
                command=lambda c=value: self.switch_category(c),
                font=('Google Sans', 10, 'bold' if value == self.current_category else 'normal'),
                bg=self.palette['selected'] if value == self.current_category else self.palette['button_bg'],
                fg=self.palette['accent'] if value == self.current_category else self.palette['text'],
                activebackground=self.palette['selected'],
                activeforeground=self.palette['text'],
                relief=tk.RIDGE,
                bd=1,
                padx=14,
                pady=8,
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.category_buttons[value] = btn

        tree_frame = tk.Frame(card, bg=self.palette['button_bg'])
        tree_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=8, pady=(0, 8))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ('select', 'star', 'sender', 'subject', 'snippet', 'time')
        self.email_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25, style='Gmail.Treeview')

        self.email_tree.heading('select', text='')
        self.email_tree.heading('star', text='')
        self.email_tree.heading('sender', text='')
        self.email_tree.heading('subject', text='')
        self.email_tree.heading('snippet', text='')
        self.email_tree.heading('time', text='')

        self.email_tree.column('select', width=30, anchor='center', stretch=False)
        self.email_tree.column('star', width=30, anchor='center', stretch=False)
        self.email_tree.column('sender', width=190, anchor='w', stretch=False)
        self.email_tree.column('subject', width=280, anchor='w')
        self.email_tree.column('snippet', width=360, anchor='w')
        self.email_tree.column('time', width=90, anchor='e', stretch=False)

        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.email_tree.yview)
        self.email_tree.configure(yscrollcommand=v_scrollbar.set)

        self.email_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.email_tree.bind('<ButtonRelease-1>', self.on_email_click)
        self.email_tree.bind('<Double-1>', self.on_email_double_click)

        self.email_tree.tag_configure('unread', font=('Google Sans', 10, 'bold'))
        self.email_tree.tag_configure('read', font=('Google Sans', 10))
    
    def create_email_content(self, parent):
        """Create email content viewing area"""
        content_frame = tk.Frame(parent, bg=self.palette['bg'])
        content_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        
        # Email content header
        content_header = tk.Frame(content_frame, bg=self.palette['bg'], height=50)
        content_header.grid(row=0, column=0, sticky=(tk.W, tk.E))
        content_header.pack_propagate(False)
        
        # Email actions
        actions_frame = tk.Frame(content_header, bg=self.palette['bg'])
        actions_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.reply_btn = tk.Button(actions_frame, text="↩️ Reply", 
                                  command=self.reply_email,
                                  font=('Google Sans', 10),
                                  bg=self.palette['bg'], fg=self.palette['text'],
                                  relief=tk.FLAT, cursor='arrow')
        self.reply_btn.pack(side=tk.LEFT, padx=5)
        
        self.forward_btn = tk.Button(actions_frame, text="↪️ Forward", 
                                    command=self.forward_email,
                                    font=('Google Sans', 10),
                                    bg=self.palette['bg'], fg=self.palette['text'],
                                    relief=tk.FLAT, cursor='arrow')
        self.forward_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(actions_frame, text="🗑️ Delete", 
                                  command=self.delete_current_email,
                                  font=('Google Sans', 10),
                                  bg=self.palette['bg'], fg=self.palette['danger'],
                                  relief=tk.FLAT, cursor='arrow')
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Email content display
        self.content_frame = tk.Frame(content_frame, bg=self.palette['bg'])
        self.content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Default message
        self.content_label = tk.Label(self.content_frame, 
                                    text="Select an email to view",
                                    font=('Google Sans', 14),
                                    fg=self.palette['muted'], bg=self.palette['bg'])
        self.content_label.pack(expand=True)
        
        # Email details (hidden by default)
        self.email_details_frame = None
    
    def create_status_bar(self, parent):
        """Create Gmail-style status bar"""
        status_frame = tk.Frame(parent, bg=self.palette['surface'], height=30)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))
        status_frame.grid_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="Ready", 
                                    font=('Google Sans', 10),
                                    fg=self.palette['muted'], bg=self.palette['surface'],
                                    anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    # Email service methods
    def start_progress(self):
        """Start progress indicator"""
        self.progress.start(10)
    
    def stop_progress(self):
        """Stop progress indicator"""
        self.progress.stop()
    
    
    def connect_gmail(self):
        """Connect to Gmail account"""
        def connect_thread():
            try:
                self.start_progress()
                self.update_status("Connecting to Gmail...")
                
                if self.gmail_service.authenticate():
                    email = self.gmail_service.get_user_email()
                    self.user_label.config(text=email)
                    self.update_status(f"Connected as {email}")
                    
                    # Load emails
                    self.load_emails()
                else:
                    self.update_status("Failed to connect to Gmail")
                    messagebox.showerror("Error", "Failed to authenticate with Gmail")
                    
            except Exception as e:
                self.update_status(f"Error connecting to Gmail: {str(e)}")
                messagebox.showerror("Error", f"Failed to connect to Gmail: {str(e)}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def load_emails(self):
        """Load emails for current folder"""
        def load_thread():
            try:
                self.start_progress()
                self.update_status(f"Loading {self.current_folder} emails...")
                self.selected_email_ids.clear()
                
                if self.current_folder == 'INBOX':
                    emails = self.gmail_service.get_emails(max_results=500)
                elif self.current_folder == 'SENT':
                    emails = self.gmail_service.get_sent_emails(max_results=500)
                elif self.current_folder == 'SNOOZED':
                    emails = self.gmail_service.get_snoozed_emails(max_results=500)
                elif self.current_folder == 'DRAFTS':
                    emails = self.gmail_service.get_draft_emails(max_results=500)
                elif self.current_folder == 'STARRED':
                    emails = self.gmail_service.get_starred_emails(max_results=500)
                elif self.current_folder == 'TRASH':
                    emails = self.gmail_service.get_trash_emails(max_results=500)
                elif self.current_folder == 'ALL':
                    emails = self.gmail_service.get_all_mail(max_results=500)
                elif self.current_folder == 'IMPORTANT':
                    emails = self.gmail_service.get_important_emails(max_results=500)
                elif self.current_folder == 'ATTACHMENTS':
                    emails = self.gmail_service.get_attachment_emails(max_results=500)
                else:
                    emails = self.gmail_service.get_emails(max_results=500)
                
                self.all_emails = emails
                self.emails = self.apply_category_filter(list(emails))
                self.populate_email_tree()
                self.update_status(f"Loaded {len(emails)} emails")
                
            except Exception as e:
                self.update_status(f"Error loading emails: {str(e)}")
                messagebox.showerror("Error", f"Failed to load emails: {str(e)}")
            finally:
                self.stop_progress()
        
        threading.Thread(target=load_thread, daemon=True).start()

    def apply_category_filter(self, emails: List[Dict]) -> List[Dict]:
        if self.current_category == 'PRIMARY':
            return [
                e for e in emails
                if 'CATEGORY_PROMOTIONS' not in e.get('labelIds', [])
                and 'CATEGORY_SOCIAL' not in e.get('labelIds', [])
            ]
        if self.current_category == 'PROMOTIONS':
            return [e for e in emails if 'CATEGORY_PROMOTIONS' in e.get('labelIds', [])]
        if self.current_category == 'SOCIAL':
            return [e for e in emails if 'CATEGORY_SOCIAL' in e.get('labelIds', [])]
        return emails

    def switch_category(self, category: str):
        self.current_category = category
        for key, btn in self.category_buttons.items():
            btn.config(
                bg=self.palette['selected'] if key == category else self.palette['bg'],
                fg=self.palette['accent'] if key == category else self.palette['muted'],
                font=('Google Sans', 10, 'bold' if key == category else 'normal'),
            )
        self.emails = self.apply_category_filter(list(self.all_emails))
        self.populate_email_tree()
    
    def populate_email_tree(self):
        """Populate email tree with current emails"""
        # Clear existing items
        for item in self.email_tree.get_children():
            self.email_tree.delete(item)
        self.email_by_id = {}
        
        # Add emails with Gmail-style formatting
        for email in self.emails:
            # Format sender name
            sender = email.get('sender', 'Unknown')
            if '<' in sender:
                sender = sender.split('<')[0].strip()
            
            # Format date
            date_str = email.get('date', '')
            try:
                # Try to parse and format date
                from datetime import datetime, timedelta
                if 'Today' in date_str or date_str == datetime.now().strftime('%Y-%m-%d'):
                    date_str = datetime.now().strftime('%I:%M %p')
                else:
                    date_str = date_str.split(' ')[0]  # Just show date
            except:
                pass
            
            # Truncate snippet
            snippet = email.get('snippet', '')
            if len(snippet) > 60:
                snippet = snippet[:60] + '...'
            
            subject = email.get('subject', 'No Subject')
            starred = '★' if 'STARRED' in email.get('labelIds', []) else '☆'

            values = (
                '☑' if email.get('id') in self.selected_email_ids else '☐',
                starred,
                sender,
                subject,
                snippet,
                date_str,
            )
            
            # Determine if email is read/unread
            tags = ('read',) if email.get('isRead', False) else ('unread',)
            email_id = email['id']
            self.email_by_id[email_id] = email
            self.email_tree.insert('', tk.END, iid=email_id, values=values, tags=tags)

        self.count_label.config(text=f"{len(self.emails)} messages")
    
    def on_email_click(self, event):
        """Handle email click for selection and viewing"""
        region = self.email_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.email_tree.identify_column(event.x)
            item = self.email_tree.identify_row(event.y)
            
            if item:
                if column == '#1':  # Checkbox column
                    current_values = self.email_tree.item(item, 'values')
                    if current_values[0] == '☐':
                        self.selected_email_ids.add(item)
                        new_values = ('☑',) + current_values[1:]
                    else:
                        self.selected_email_ids.discard(item)
                        new_values = ('☐',) + current_values[1:]
                    
                    self.email_tree.item(item, values=new_values)
                elif column == '#2':
                    # local star toggle
                    values = list(self.email_tree.item(item, 'values'))
                    values[1] = '☆' if values[1] == '★' else '★'
                    self.email_tree.item(item, values=tuple(values))
                else:
                    email = self.email_by_id.get(item)
                    if email:
                        self.show_email_preview(email)
                        if not email.get('isRead', False):
                            email['isRead'] = True
                            self.email_tree.item(item, tags=('read',))
    
    def on_email_double_click(self, event):
        """Handle email double click for compose reply"""
        item = self.email_tree.identify_row(event.y)
        if item:
            email = self.email_by_id.get(item)
            if email:
                self.reply_email()
    
    
    def filter_emails(self, event=None):
        """Filter emails based on search term"""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.emails = self.apply_category_filter(list(self.all_emails))
            self.populate_email_tree()
            return
        
        category_emails = self.apply_category_filter(list(self.all_emails))
        filtered_emails = [
            email for email in category_emails
            if search_term in email.get('sender', '').lower() or
               search_term in email.get('subject', '').lower() or
               search_term in email.get('snippet', '').lower()
        ]
        self.emails = filtered_emails
        self.populate_email_tree()
    
    def sort_emails(self, event=None):
        """Sort emails by selected criteria"""
        sort_by = self.sort_var.get()
        
        if sort_by == "sender":
            self.emails.sort(key=lambda x: x.get('sender', ''))
        elif sort_by == "date":
            self.emails.sort(key=lambda x: x.get('date', ''), reverse=True)
        elif sort_by == "subject":
            self.emails.sort(key=lambda x: x.get('subject', ''))
        
        self.populate_email_tree()
    
    def select_all_emails(self):
        """Select all emails in the list"""
        self.selected_email_ids = {item for item in self.email_tree.get_children()}
        for item in self.email_tree.get_children():
            values = self.email_tree.item(item, 'values')
            self.email_tree.item(item, values=('☑',) + values[1:])
    
    def deselect_all_emails(self):
        """Deselect all emails in the list"""
        self.selected_email_ids.clear()
        for item in self.email_tree.get_children():
            values = self.email_tree.item(item, 'values')
            self.email_tree.item(item, values=('☐',) + values[1:])
    
    def get_selected_emails(self):
        """Get list of selected email IDs"""
        return list(self.selected_email_ids)
    
    def delete_selected_emails(self, email_ids=None):
        """Delete selected emails or specific email IDs"""
        if email_ids is None:
            selected_ids = self.get_selected_emails()
        else:
            selected_ids = email_ids
        
        if not selected_ids:
            messagebox.showwarning("Warning", "No emails selected for deletion")
            return
        
        count = len(selected_ids)
        if count == 1:
            message = "Delete this email?"
        else:
            message = f"Delete {count} selected emails?"
        
        if messagebox.askyesno("Confirm Delete", message):
            def delete_thread():
                try:
                    self.start_progress()
                    self.update_status(f"Deleting {count} emails...")
                    
                    success_count = self.gmail_service.delete_emails(selected_ids)
                    
                    # Remove from local list and refresh
                    self.selected_email_ids.clear()
                    self.all_emails = [e for e in self.all_emails if e['id'] not in selected_ids]
                    self.emails = [e for e in self.emails if e['id'] not in selected_ids]
                    self.populate_email_tree()
                    
                    self.update_status(f"Successfully deleted {success_count} emails")
                    messagebox.showinfo("Success", f"Deleted {success_count} emails")
                    
                    if hasattr(self, 'current_email') and self.current_email and self.current_email['id'] in selected_ids:
                        self.current_email = None
                    
                except Exception as e:
                    self.update_status(f"Error deleting emails: {str(e)}")
                    messagebox.showerror("Error", f"Failed to delete emails: {str(e)}")
                finally:
                    self.stop_progress()
            
            threading.Thread(target=delete_thread, daemon=True).start()
    
    def clear_all_from_sender(self):
        """Clear all emails from selected sender"""
        # Get unique senders
        senders = list(set(email.get('sender', '') for email in self.emails))
        
        if not senders:
            messagebox.showwarning("Warning", "No emails available")
            return
        
        # Create sender selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Sender")
        dialog.geometry("300x400")
        
        ttk.Label(dialog, text="Select sender to clear all emails:").pack(pady=10)
        
        sender_var = tk.StringVar()
        sender_listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
        sender_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for sender in sorted(senders):
            sender_listbox.insert(tk.END, sender)
        
        def confirm_clear():
            selection = sender_listbox.curselection()
            if selection:
                selected_sender = sender_listbox.get(selection[0])
                dialog.destroy()
                
                # Count emails from this sender
                sender_emails = [e for e in self.emails if e.get('sender', '') == selected_sender]
                sender_ids = [e['id'] for e in sender_emails]
                
                if messagebox.askyesno("Confirm Clear All", 
                                      f"Clear all {len(sender_emails)} emails from {selected_sender}?"):
                    def clear_thread():
                        try:
                            self.start_progress()
                            self.update_status(f"Clearing all emails from {selected_sender}...")
                            
                            success_count = self.gmail_service.delete_emails(sender_ids)
                            
                            # Remove from local list and refresh
                            self.all_emails = [e for e in self.all_emails if e.get('sender', '') != selected_sender]
                            self.emails = [e for e in self.emails if e.get('sender', '') != selected_sender]
                            self.populate_email_tree()
                            
                            self.update_status(f"Cleared {success_count} emails from {selected_sender}")
                            messagebox.showinfo("Success", f"Cleared {success_count} emails from {selected_sender}")
                            
                        except Exception as e:
                            self.update_status(f"Error clearing emails: {str(e)}")
                            messagebox.showerror("Error", f"Failed to clear emails: {str(e)}")
                        finally:
                            self.stop_progress()
                    
                    threading.Thread(target=clear_thread, daemon=True).start()
        
        ttk.Button(dialog, text="Clear All", command=confirm_clear).pack(pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def refresh_gmail(self):
        """Refresh Gmail emails"""
        if self.gmail_service.is_authenticated():
            self.load_emails()
    
    def auto_connect(self):
        """Auto-connect to Gmail if credentials available"""
        if os.path.exists('gmail_credentials.json'):
            try:
                with open('gmail_credentials.json', 'r') as f:
                    creds = json.load(f)
                    if 'YOUR_GMAIL_CLIENT_ID_HERE' not in str(creds):
                        self.connect_gmail()
            except:
                pass
    
    def switch_folder(self, folder):
        """Switch between Gmail folders"""
        # Update button colors
        for f, btn in self.folder_buttons.items():
            btn.config(bg=self.palette['surface'])
        self.folder_buttons[folder].config(bg=self.palette['selected'])
        
        self.current_folder = folder
        self.load_emails()
    
    def open_compose(self):
        """Open compose email window"""
        compose_window = tk.Toplevel(self.root)
        compose_window.title("New Message")
        compose_window.geometry("600x500")
        compose_window.configure(bg=self.palette['bg'])
        
        # To field
        to_frame = tk.Frame(compose_window, bg=self.palette['bg'])
        to_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(to_frame, text="To:", font=('Google Sans', 12),
                fg=self.palette['text'], bg=self.palette['bg']).pack(side=tk.LEFT)
        
        self.to_entry = tk.Entry(to_frame, font=('Google Sans', 12), width=50)
        self.to_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Subject field
        subject_frame = tk.Frame(compose_window, bg=self.palette['bg'])
        subject_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(subject_frame, text="Subject:", font=('Google Sans', 12),
                fg=self.palette['text'], bg=self.palette['bg']).pack(side=tk.LEFT)
        
        self.subject_entry = tk.Entry(
            subject_frame,
            font=('Google Sans', 12),
            width=50,
            bg=self.palette['input_bg'],
            fg=self.palette['input_fg'],
            insertbackground=self.palette['input_fg'],
        )
        self.subject_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Message body
        body_frame = tk.Frame(compose_window, bg=self.palette['bg'])
        body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.body_text = scrolledtext.ScrolledText(body_frame, wrap=tk.WORD, 
                                                   font=('Google Sans', 12),
                                                   bg=self.palette['input_bg'], fg=self.palette['input_fg'])
        self.body_text.pack(fill=tk.BOTH, expand=True)
        
        # Send button
        send_frame = tk.Frame(compose_window, bg=self.palette['bg'])
        send_frame.pack(fill=tk.X, padx=10, pady=10)
        
        send_btn = tk.Button(send_frame, text="Send", 
                           command=lambda: self.send_email(compose_window),
                           font=('Google Sans', 12, 'bold'),
                           bg=self.palette['header'], fg='white',
                           relief=tk.FLAT, padx=20, pady=8,
                           cursor='arrow')
        send_btn.pack(side=tk.RIGHT)
    
    def send_email(self, window):
        """Send email"""
        to = self.to_entry.get()
        subject = self.subject_entry.get()
        body = self.body_text.get('1.0', tk.END).strip()
        
        if not to or not subject or not body:
            messagebox.showwarning("Warning", "Please fill in all fields")
            return
        
        try:
            if self.gmail_service.send_email(to, subject, body):
                messagebox.showinfo("Success", "Email sent successfully!")
                window.destroy()
                # Refresh sent folder
                if self.current_folder == 'SENT':
                    self.load_emails()
            else:
                messagebox.showerror("Error", "Failed to send email")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {str(e)}")
    
    def reply_email(self):
        """Reply to current email"""
        if hasattr(self, 'current_email') and self.current_email:
            self.open_compose()
            # Pre-fill with reply details
            self.to_entry.insert(0, self.current_email.get('sender', ''))
            self.subject_entry.insert(0, f"Re: {self.current_email.get('subject', '')}")
    
    def forward_email(self):
        """Forward current email"""
        if hasattr(self, 'current_email') and self.current_email:
            self.open_compose()
            self.subject_entry.insert(0, f"Fwd: {self.current_email.get('subject', '')}")
    
    def delete_current_email(self):
        """Delete current email"""
        if hasattr(self, 'current_email') and self.current_email:
            self.delete_selected_emails([self.current_email['id']])
    
    def show_email_preview(self, email):
        """Open an email preview popup while keeping inbox-style list UI."""
        self.current_email = email

        preview = tk.Toplevel(self.root)
        preview.title(email.get('subject', 'Email'))
        preview.geometry('860x640')
        preview.configure(bg=self.palette['bg'])

        header = tk.Frame(preview, bg=self.palette['bg'])
        header.pack(fill=tk.X, padx=16, pady=12)

        tk.Label(
            header,
            text=email.get('subject', '(No subject)'),
            font=('Google Sans', 14, 'bold'),
            fg=self.palette['text'],
            bg=self.palette['bg'],
            anchor='w',
        ).pack(fill=tk.X)

        meta = tk.Label(
            header,
            text=f"From: {email.get('sender', '')}    •    {email.get('date', '')}",
            font=('Google Sans', 10),
            fg=self.palette['muted'],
            bg=self.palette['bg'],
            anchor='w',
        )
        meta.pack(fill=tk.X, pady=(6, 0))

        body = scrolledtext.ScrolledText(
            preview,
            wrap=tk.WORD,
            font=('Google Sans', 11),
            bg=self.palette['input_bg'],
            fg=self.palette['input_fg'],
            insertbackground=self.palette['input_fg'],
        )
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        full_body = email.get('body') or self.gmail_service.get_email_body(email['id'])
        body.insert('1.0', full_body or email.get('snippet', 'No content available'))
        body.config(state=tk.DISABLED)
    

def main():
    root = tk.Tk()
    app = GmailOrganizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
