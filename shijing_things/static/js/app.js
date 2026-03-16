/**
 * 诗经事物 - 前端 JavaScript
 * 纯 vanilla JS，无框架依赖
 */

(function() {
    'use strict';

    // ===== DOM 元素 =====
    const modal = document.getElementById('detail-modal');
    const modalBody = document.getElementById('modal-body');
    const modalClose = document.querySelector('.modal-close');

    // ===== 初始化 =====
    function init() {
        bindEvents();
        loadImages();
    }

    // ===== 事件绑定 =====
    function bindEvents() {
        // 卡片点击事件 - 使用事件委托
        document.addEventListener('click', function(e) {
            const card = e.target.closest('.item-card');
            if (card) {
                const itemId = card.dataset.id;
                if (itemId) {
                    // 跳转到详情页
                    window.location.href = `/item/${itemId}`;
                }
            }
        });

        // 弹窗关闭
        if (modalClose) {
            modalClose.addEventListener('click', closeModal);
        }

        // 点击弹窗外部关闭
        if (modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // ESC 键关闭弹窗
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    }

    // ===== 弹窗控制 =====
    function openModal(content) {
        if (modalBody) {
            modalBody.innerHTML = content;
        }
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeModal() {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    // ===== 异步加载详情（可选功能）=====
    async function loadItemDetail(itemId) {
        try {
            const response = await fetch(`/api/items/${itemId}`);
            if (!response.ok) throw new Error('加载失败');
            const item = await response.json();
            return item;
        } catch (err) {
            console.error('加载详情失败:', err);
            return null;
        }
    }

    // ===== 图片懒加载 =====
    function loadImages() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src || img.src;
                        observer.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        }
    }

    // ===== 搜索防抖 =====
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ===== 表单验证 =====
    function validateForm(form) {
        const required = form.querySelectorAll('[required]');
        let valid = true;

        required.forEach(field => {
            if (!field.value.trim()) {
                valid = false;
                field.classList.add('error');
            } else {
                field.classList.remove('error');
            }
        });

        return valid;
    }

    // ===== API 工具函数 =====
    window.API = {
        // 获取事物列表
        async getItems(filters = {}) {
            const params = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value) params.append(key, value);
            });
            
            const response = await fetch(`/api/items/?${params}`);
            return response.json();
        },

        // 获取单个事物
        async getItem(id) {
            const response = await fetch(`/api/items/${id}`);
            return response.json();
        },

        // 创建事物
        async createItem(data) {
            const response = await fetch('/api/items/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            return response.json();
        },

        // 更新事物
        async updateItem(id, data) {
            const response = await fetch(`/api/items/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            return response.json();
        },

        // 删除事物
        async deleteItem(id) {
            const response = await fetch(`/api/items/${id}`, {
                method: 'DELETE',
            });
            return response.ok;
        },

        // 获取统计数据
        async getStats() {
            const response = await fetch('/api/items/stats');
            return response.json();
        },
    };

    // ===== DOM 工具函数 =====
    window.DOM = {
        // 创建元素
        create(tag, attrs = {}, children = []) {
            const el = document.createElement(tag);
            Object.entries(attrs).forEach(([key, value]) => {
                if (key === 'className') {
                    el.className = value;
                } else if (key.startsWith('on') && typeof value === 'function') {
                    el.addEventListener(key.slice(2).toLowerCase(), value);
                } else {
                    el.setAttribute(key, value);
                }
            });
            children.forEach(child => {
                if (typeof child === 'string') {
                    el.appendChild(document.createTextNode(child));
                } else if (child) {
                    el.appendChild(child);
                }
            });
            return el;
        },

        // 选择器
        $(selector, context = document) {
            return context.querySelector(selector);
        },

        $$(selector, context = document) {
            return Array.from(context.querySelectorAll(selector));
        },
    };

    // ===== 启动 =====
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
