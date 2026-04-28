// 模拟前端API调用测试
const axios = require('axios');

const api = axios.create({
  baseURL: 'http://localhost:8879/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 先登录获取token
async function login() {
  try {
    const response = await api.post('/auth/login', {
      username: 'admin',
      password: 'admin123'
    });
    return response.data.access_token;
  } catch (error) {
    console.error('Login error:', error.response?.data || error.message);
    return null;
  }
}

// 测试获取应用的仪表盘数据
async function testDashboardData() {
  const token = await login();
  if (!token) {
    console.error('Failed to login');
    return;
  }

  // 设置token
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

  try {
    // 获取应用列表
    const appsResponse = await api.get('/apps/');
    const apps = appsResponse.data;
    console.log('Apps:', apps);

    if (apps.length === 0) {
      console.error('No apps found');
      return;
    }

    const appId = apps[0].id;
    console.log('Testing app:', appId, apps[0].name);

    // 获取仪表盘配置
    const dashboardResponse = await api.get(`/apps/${appId}/dashboard`);
    console.log('Dashboard config:', JSON.stringify(dashboardResponse.data, null, 2));

    // 测试获取组件数据
    if (dashboardResponse.data.data && dashboardResponse.data.data.pages) {
      const pages = dashboardResponse.data.data.pages;
      for (const page of pages) {
        if (page.widgets) {
          for (const widget of page.widgets) {
            if (widget.data_source && widget.data_source.template_id) {
              console.log(`\nTesting widget: ${widget.title} (${widget.type})`);
              try {
                const widgetResponse = await api.post('/apps/dashboard/widget/data', widget);
                console.log('Widget data:', JSON.stringify(widgetResponse.data, null, 2));
              } catch (error) {
                console.error('Error getting widget data:', error.response?.data || error.message);
              }
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('Test error:', error.response?.data || error.message);
  }
}

testDashboardData();
