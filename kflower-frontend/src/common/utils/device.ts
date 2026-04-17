/**
 * 设备检测工具
 */

// 检测是否为移动设备
export function isMobileDevice(): boolean {
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera
  
  const mobileRegex = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i
  const isMobileUA = mobileRegex.test(userAgent.toLowerCase())
  
  // 通过屏幕宽度检测
  const isNarrowScreen = window.innerWidth < 768
  
  // 通过触摸能力检测
  const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0
  
  return isMobileUA || (isNarrowScreen && isTouchDevice)
}

// 检测是否为平板
export function isTabletDevice(): boolean {
  const isMobile = isMobileDevice()
  const isNarrow = window.innerWidth >= 768 && window.innerWidth < 1024
  return isMobile && isNarrow
}

// 检测是否为PC
export function isPCDevice(): boolean {
  return !isMobileDevice()
}

// 设备检测入口函数
export function checkDevice() {
  return isMobileDevice()
}

// 获取设备类型
export function getDeviceType(): 'mobile' | 'tablet' | 'pc' {
  if (isMobileDevice()) {
    return isTabletDevice() ? 'tablet' : 'mobile'
  }
  return 'pc'
}

// 获取路由基础路径
export function getRouterBase(): string {
  const deviceType = getDeviceType()
  if (deviceType === 'mobile') {
    return '/app'
  }
  return '/pc'
}
