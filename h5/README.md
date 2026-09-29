# Pi Agent H5

Node.js 18+；在 `h5/` 下运行：

```sh
npm install
npm run dev
npm run typecheck
npm run build
npm run preview
```

开发服务器将 `/api` 代理至 `http://127.0.0.1:8000`。`npm run build` 会清空并写入 Python 包内的 `../src/gs_openapi/server/static/`，由 HTTP 服务同源提供页面和资源。页面使用 hash 路由，避免静态服务缺少历史路由回退。设置页可保存服务地址及 API Key（浏览器 localStorage）；请仅在可信设备和 HTTPS 环境中使用密钥。
