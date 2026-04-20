<template>
  <div class="workflow-designer">
    <div class="designer-header">
      <el-page-header :title="workflowName" @back="goBack">
        <template #content>
          <div class="header-actions">
            <el-button type="primary" @click="saveWorkflow">
              <el-icon><Check /></el-icon> 保存
            </el-button>
            <el-button @click="validateWorkflow">
              <el-icon><CircleCheck /></el-icon> 验证
            </el-button>
            <el-button @click="previewWorkflow">
              <el-icon><View /></el-icon> 预览
            </el-button>
          </div>
        </template>
      </el-page-header>
    </div>
    
    <div class="designer-body">
      <!-- 左侧工具栏 -->
      <div class="toolbox">
        <h4>流程节点</h4>
        <div class="node-list">
          <div
            v-for="node in nodeTypes"
            :key="node.type"
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <el-icon :size="20"><component :is="node.icon" /></el-icon>
            <span>{{ node.name }}</span>
          </div>
        </div>
      </div>
      
      <!-- 中间画布 -->
      <div
        class="canvas"
        ref="canvasRef"
        @dragover.prevent
        @drop="handleDrop"
        @click="deselectNode"
      >
        <svg class="connections" ref="connectionsSvg">
          <path
            v-for="conn in connections"
            :key="conn.id"
            :d="conn.path"
            class="connection-line"
            :class="{ selected: selectedConnection === conn.id }"
            @click.stop="selectConnection(conn.id)"
          />
          <!-- 连线预览 -->
          <path
            v-if="isConnecting && connectionStart && previewPath"
            :d="previewPath"
            class="connection-line preview"
          />
        </svg>
        
        <div
          v-for="node in nodes"
          :key="node.id"
          class="workflow-node"
          :class="{ selected: selectedNode === node.id }"
          :style="{ left: node.x + 'px', top: node.y + 'px' }"
          @mousedown="startDrag($event, node)"
          @click.stop="selectNode(node.id)"
        >
          <div class="node-header" :class="node.type">
            <el-icon><component :is="getNodeIcon(node.type)" /></el-icon>
            <span>{{ node.name }}</span>
          </div>
          <div class="node-body">
            <p>{{ node.description || '暂无描述' }}</p>
          </div>
          <div class="node-ports">
            <div class="input-ports">
              <div
                class="port input"
                @mousedown.stop="startConnection($event, node.id, 'input')"
              />
            </div>
            <div class="output-ports">
              <div
                class="port output"
                @mousedown.stop="startConnection($event, node.id, 'output')"
              />
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧属性面板 -->
      <div class="properties">
        <h4>属性配置</h4>
        <div v-if="selectedNodeData" class="property-form">
          <el-tabs v-model="activePropertyTab">
            <el-tab-pane label="基本属性" name="basic">
              <el-form label-width="100px">
                <el-form-item label="节点名称">
                  <el-input v-model="selectedNodeData.name" />
                </el-form-item>
                <el-form-item label="节点描述">
                  <el-input v-model="selectedNodeData.description" type="textarea" :rows="2" />
                </el-form-item>
                <!-- 表单模板绑定 -->
                <el-form-item label="绑定表单" v-if="['approval', 'task', 'cc', 'data_fill', 'trigger', 'data_change', 'add_data', 'update_data', 'delete_data'].includes(selectedNodeData.type)">
                  <el-select
                    v-model="nodeConfig.form_template_id"
                    placeholder="选择表单模板"
                    filterable
                    style="width: 100%"
                    @change="handleTemplateChange"
                  >
                    <el-option label="不绑定表单" :value="undefined" />
                    <el-option
                      v-for="template in templates"
                      :key="template.id"
                      :label="`${template.name} (ID: ${template.id})`"
                      :value="template.id"
                    />
                  </el-select>
                  <div class="form-tip">选择此节点操作的表单模板</div>
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 审批节点配置 - 斑斑低代码平台标准 -->
            <el-tab-pane label="审批配置" name="approval" v-if="['approval', 'task', 'cc'].includes(selectedNodeData.type)">
              <el-form label-width="120px" class="node-config-form">
                <!-- 审批类型（仅审批节点有自动通过/拒绝） -->
                <el-form-item label="审批类型" v-if="selectedNodeData.type === 'approval'">
                  <el-radio-group v-model="nodeConfig.approval_type">
                    <el-radio-button value="manual">人工审批</el-radio-button>
                    <el-radio-button value="auto_approve">自动通过</el-radio-button>
                    <el-radio-button value="auto_reject">自动拒绝</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                
                <!-- 人工审批配置 -->
                <template v-if="selectedNodeData.type !== 'approval' || nodeConfig.approval_type === 'manual'">
                  <!-- 审批方式（仅审批节点） -->
                  <el-form-item label="审批方式" v-if="selectedNodeData.type === 'approval'">
                    <el-radio-group v-model="nodeConfig.approval_mode">
                      <el-radio-button value="regular">常规审批</el-radio-button>
                      <el-radio-button value="hierarchical">逐级审批</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  
                  <!-- 逐级审批顺序 -->
                  <el-form-item label="审批顺序" v-if="nodeConfig.approval_mode === 'hierarchical'">
                    <el-radio-group v-model="nodeConfig.hierarchical_order">
                      <el-radio-button value="bottom_up">自下而上</el-radio-button>
                      <el-radio-button value="top_down">自上而下</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  
                  <!-- 人员来源（逐级审批不需要设置审批人来源） -->
                  <template v-if="nodeConfig.approval_mode !== 'hierarchical'">
                    <el-form-item :label="selectedNodeData.type === 'cc' ? '抄送人来源' : (selectedNodeData.type === 'task' ? '办理人来源' : '审批人来源')">
                      <el-select v-model="nodeConfig.assignee_source" placeholder="选择人员来源" style="width:100%">
                        <el-option label="提交人自己" value="submitter" />
                        <el-option label="指定成员/角色" value="specified" />
                        <el-option label="部门主管" value="department_manager" />
                        <el-option label="表单内成员字段" value="form_member_field" />
                        <el-option label="表单内部门字段" value="form_department_field" />
                      </el-select>
                    </el-form-item>
                    
                    <!-- 指定成员/角色 -->
                    <template v-if="nodeConfig.assignee_source === 'specified'">
                      <el-form-item :label="selectedNodeData.type === 'cc' ? '抄送人' : (selectedNodeData.type === 'task' ? '办理人' : '审批人')">
                        <el-select
                          v-model="nodeConfig.assignee_ids"
                          multiple
                          placeholder="选择用户或角色"
                          filterable
                          style="width: 100%"
                        >
                          <el-option-group label="用户">
                            <el-option
                              v-for="user in users"
                              :key="`user-${user.id}`"
                              :label="`${user.full_name || user.username} (${user.username})`"
                              :value="`user:${user.id}`"
                            />
                          </el-option-group>
                          <el-option-group label="角色">
                            <el-option
                              v-for="role in roles"
                              :key="`role-${role.id}`"
                              :label="role.name"
                              :value="`role:${role.id}`"
                            />
                          </el-option-group>
                        </el-select>
                        <div class="form-tip" v-if="!users.length">⚠ 暂无用户数据，请检查用户API</div>
                      </el-form-item>
                      
                      <el-form-item label="多人处理方式" v-if="nodeConfig.assignee_ids && nodeConfig.assignee_ids.length > 1">
                        <el-radio-group v-model="nodeConfig.multi_person_mode">
                          <el-radio-button value="all">会签</el-radio-button>
                          <el-radio-button value="any">或签</el-radio-button>
                          <el-radio-button value="sequential">依次处理</el-radio-button>
                        </el-radio-group>
                        <div class="form-tip">
                          会签：需所有人同意 | 或签：一人同意即可 | 依次处理：按顺序逐一处理
                        </div>
                      </el-form-item>
                    </template>
                    
                    <!-- 部门主管配置 -->
                    <template v-if="nodeConfig.assignee_source === 'department_manager'">
                      <el-form-item label="主管选择方式">
                        <el-radio-group v-model="nodeConfig.manager_order">
                          <el-radio-button value="bottom_up">自下而上</el-radio-button>
                          <el-radio-button value="top_down">自上而下</el-radio-button>
                        </el-radio-group>
                      </el-form-item>
                      <el-form-item label="主管级别">
                        <el-select v-model="nodeConfig.manager_level" placeholder="选择主管级别" style="width:100%">
                          <el-option label="直接主管（第1级）" value="direct" />
                          <el-option label="二级主管" value="level2" />
                          <el-option label="三级主管" value="level3" />
                          <el-option label="顶级主管" value="top" />
                        </el-select>
                      </el-form-item>
                    </template>
                    
                    <!-- 表单内成员/部门字段 -->
                    <template v-if="nodeConfig.assignee_source === 'form_member_field' || nodeConfig.assignee_source === 'form_department_field'">
                      <el-form-item label="选择字段">
                        <el-select
                          v-model="nodeConfig.assignee_field"
                          placeholder="选择表单字段"
                          style="width: 100%"
                        >
                          <el-option label="请先在基本属性中绑定表单" value="" disabled v-if="!nodeConfig.form_template_id" />
                          <el-option 
                            v-for="field in getTemplateFields(nodeConfig.form_template_id)"
                            :key="field.name"
                            :label="`${field.label || field.name} (${field.type})`"
                            :value="field.name"
                          />
                        </el-select>
                      </el-form-item>
                    </template>
                  </template>

                  <!-- 审批人为空时的处理 -->
                  <el-divider content-position="left" v-if="selectedNodeData.type !== 'cc'">
                    <span class="divider-title">{{ selectedNodeData.type === 'task' ? '办理人为空时' : '审批人为空时' }}</span>
                  </el-divider>
                  <el-form-item label="为空处理方式" v-if="selectedNodeData.type !== 'cc'">
                    <el-select v-model="nodeConfig.empty_assignee_action" placeholder="选择处理方式" style="width:100%">
                      <el-option label="自动通过" value="auto_approve" v-if="selectedNodeData.type === 'approval'" />
                      <el-option label="指定人员处理" value="specified_fallback" />
                      <el-option label="转交给管理员" value="admin_fallback" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="指定备用人员" v-if="nodeConfig.empty_assignee_action === 'specified_fallback' && selectedNodeData.type !== 'cc'">
                    <el-select v-model="nodeConfig.fallback_assignee_id" placeholder="选择备用处理人" filterable style="width:100%">
                      <el-option
                        v-for="user in users"
                        :key="user.id"
                        :label="`${user.full_name || user.username} (${user.username})`"
                        :value="user.id"
                      />
                    </el-select>
                  </el-form-item>

                  <!-- 审批人与提交人相同时的处理（仅审批节点） -->
                  <el-divider content-position="left" v-if="selectedNodeData.type === 'approval'">
                    <span class="divider-title">审批人与提交人相同时</span>
                  </el-divider>
                  <el-form-item label="相同时处理" v-if="selectedNodeData.type === 'approval'">
                    <el-select v-model="nodeConfig.same_person_action" placeholder="选择处理方式" style="width:100%">
                      <el-option label="由提交人对自己审批" value="self_approve" />
                      <el-option label="转交给部门负责人" value="to_department_manager" />
                      <el-option label="自动跳过" value="auto_skip" />
                    </el-select>
                    <div class="form-tip">自动跳过：单人审批会自动通过，多人审批自动到下一人</div>
                  </el-form-item>
                  
                  <!-- 操作权限 -->
                  <el-divider content-position="left">
                    <span class="divider-title">操作权限</span>
                  </el-divider>
                  <el-form-item label="允许转交">
                    <el-switch v-model="nodeConfig.allow_transfer" />
                  </el-form-item>
                  <el-form-item label="必须填写意见">
                    <el-switch v-model="nodeConfig.require_comment" />
                  </el-form-item>
                  <!-- 退回配置（仅审批节点） -->
                  <template v-if="selectedNodeData.type === 'approval'">
                    <el-form-item label="允许退回">
                      <el-switch v-model="nodeConfig.allow_reject_back" />
                    </el-form-item>
                    <el-form-item label="退回范围" v-if="nodeConfig.allow_reject_back">
                      <el-radio-group v-model="nodeConfig.reject_back_range">
                        <el-radio-button value="any">不限制范围</el-radio-button>
                        <el-radio-button value="limited">限制退回节点</el-radio-button>
                      </el-radio-group>
                    </el-form-item>
                    <el-form-item label="最远退回到" v-if="nodeConfig.allow_reject_back && nodeConfig.reject_back_range === 'limited'">
                      <el-select v-model="nodeConfig.reject_back_node_id" placeholder="选择节点" style="width:100%">
                        <el-option
                          v-for="node in nodes.filter(n => n.id !== selectedNode)"
                          :key="node.id"
                          :label="node.name"
                          :value="node.id"
                        />
                      </el-select>
                    </el-form-item>
                  </template>
                  
                  <!-- 超时设置 -->
                  <el-divider content-position="left">
                    <span class="divider-title">超时设置</span>
                  </el-divider>
                  <el-form-item label="超时时间(小时)">
                    <el-input-number v-model="nodeConfig.timeout_hours" :min="0" :step="1" style="width:140px" />
                    <span class="unit-label">小时（0为不限制）</span>
                  </el-form-item>
                  <el-form-item label="超时动作">
                    <el-select v-model="nodeConfig.timeout_action" placeholder="选择超时动作" style="width:100%">
                      <el-option label="通知管理员" value="notify" />
                      <el-option label="自动通过" value="auto_approve" />
                      <el-option label="自动拒绝" value="auto_reject" />
                    </el-select>
                  </el-form-item>
                </template>
              </el-form>
            </el-tab-pane>
            
            <!-- 数据填报节点配置 -->
            <el-tab-pane label="填报配置" name="data_fill_config" v-if="selectedNodeData.type === 'data_fill'">
              <el-form label-width="120px" class="node-config-form">

                <!-- ── 填报人 ── -->
                <el-divider content-position="left">
                  <span class="divider-title">填报人</span>
                </el-divider>
                <el-form-item label="填报人来源">
                  <el-select v-model="nodeConfig.assignee_source" placeholder="选择填报人来源" style="width:100%">
                    <el-option label="提交人自己" value="submitter" />
                    <el-option label="指定成员/角色" value="specified" />
                    <el-option label="部门主管" value="department_manager" />
                    <el-option label="表单内成员字段" value="form_member_field" />
                    <el-option label="表单内部门字段" value="form_department_field" />
                  </el-select>
                </el-form-item>

                <!-- 指定成员/角色 -->
                <template v-if="nodeConfig.assignee_source === 'specified'">
                  <el-form-item label="选择填报人">
                    <el-select
                      v-model="nodeConfig.assignee_ids"
                      multiple
                      placeholder="选择用户或角色"
                      filterable
                      style="width:100%"
                    >
                      <el-option-group label="用户">
                        <el-option
                          v-for="user in users"
                          :key="`user-${user.id}`"
                          :label="`${user.full_name || user.username} (${user.username})`"
                          :value="`user:${user.id}`"
                        />
                      </el-option-group>
                      <el-option-group label="角色">
                        <el-option
                          v-for="role in roles"
                          :key="`role-${role.id}`"
                          :label="role.name"
                          :value="`role:${role.id}`"
                        />
                      </el-option-group>
                    </el-select>
                    <div class="form-tip">💡 选择部门时，请进入部门内部选择具体成员</div>
                  </el-form-item>
                </template>

                <!-- 部门主管配置 -->
                <template v-if="nodeConfig.assignee_source === 'department_manager'">
                  <el-form-item label="主管选择方式">
                    <el-radio-group v-model="nodeConfig.manager_order">
                      <el-radio-button value="bottom_up">自下而上</el-radio-button>
                      <el-radio-button value="top_down">自上而下</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item label="主管级别">
                    <el-select v-model="nodeConfig.manager_level" placeholder="选择主管级别" style="width:100%">
                      <el-option label="直接主管（第1级）" value="direct" />
                      <el-option label="二级主管" value="level2" />
                      <el-option label="三级主管" value="level3" />
                      <el-option label="顶级主管" value="top" />
                    </el-select>
                  </el-form-item>
                </template>

                <!-- 表单内成员/部门字段 -->
                <template v-if="nodeConfig.assignee_source === 'form_member_field' || nodeConfig.assignee_source === 'form_department_field'">
                  <el-form-item label="选择字段">
                    <el-select v-model="nodeConfig.assignee_field" placeholder="选择表单字段" style="width:100%">
                      <el-option label="请先在基本属性中绑定表单" value="" disabled v-if="!nodeConfig.form_template_id" />
                      <el-option
                        v-for="field in getTemplateFields(nodeConfig.form_template_id)"
                        :key="field.name"
                        :label="`${field.label || field.name} (${field.type})`"
                        :value="field.name"
                      />
                    </el-select>
                    <div class="form-tip">{{ nodeConfig.assignee_source === 'form_member_field' ? '该成员字段中选择的成员将作为填报人' : '该部门字段所在部门的主管将作为填报人' }}</div>
                  </el-form-item>
                </template>

                <!-- ── 办理人为空时 ── -->
                <el-divider content-position="left">
                  <span class="divider-title">办理人为空时</span>
                </el-divider>
                <el-form-item label="为空处理方式">
                  <el-select v-model="nodeConfig.empty_assignee_action" placeholder="选择处理方式" style="width:100%">
                    <el-option label="指定人员办理" value="specified_fallback" />
                    <el-option label="转交给管理员" value="admin_fallback" />
                  </el-select>
                </el-form-item>
                <el-form-item label="指定备用人员" v-if="nodeConfig.empty_assignee_action === 'specified_fallback'">
                  <el-select v-model="nodeConfig.fallback_assignee_id" placeholder="选择备用处理人" filterable style="width:100%">
                    <el-option
                      v-for="user in users"
                      :key="user.id"
                      :label="`${user.full_name || user.username} (${user.username})`"
                      :value="user.id"
                    />
                  </el-select>
                </el-form-item>

                <!-- ── 操作权限 ── -->
                <el-divider content-position="left">
                  <span class="divider-title">操作权限</span>
                </el-divider>
                <el-form-item label="允许转交">
                  <el-switch v-model="nodeConfig.allow_transfer" />
                  <span class="unit-label" style="margin-left:8px;color:#909399;font-size:12px;">允许填报人将任务转交给其他人</span>
                </el-form-item>
                <el-form-item label="必须填写意见">
                  <el-switch v-model="nodeConfig.require_comment" />
                </el-form-item>
                <el-form-item label="超时时间(小时)">
                  <el-input-number v-model="nodeConfig.timeout_hours" :min="0" :step="1" style="width:140px" />
                  <span class="unit-label">小时（0为不限制）</span>
                </el-form-item>
                <el-form-item label="超时动作">
                  <el-select v-model="nodeConfig.timeout_action" placeholder="选择超时动作" style="width:100%">
                    <el-option label="通知管理员" value="notify" />
                    <el-option label="自动跳过" value="auto_skip" />
                  </el-select>
                </el-form-item>

                <!-- ── 填报结束条件 ── -->
                <el-divider content-position="left">
                  <span class="divider-title">填报结束条件</span>
                </el-divider>
                <el-form-item label="启用结束条件">
                  <el-switch v-model="nodeConfig.enable_finish_condition" />
                  <div class="form-tip">开启后，满足条件时填报节点才能结束，否则流程一直停留在该节点，填报人需反复提交新数据</div>
                </el-form-item>

                <template v-if="nodeConfig.enable_finish_condition">
                  <!-- 数据源表单 -->
                  <el-divider content-position="left" style="margin-top:0">
                    <span class="divider-title" style="font-size:13px">数据源表单</span>
                  </el-divider>
                  <div class="form-tip" style="margin-bottom:8px;">默认包含本条数据，可添加其他表单作为判断条件的数据来源</div>
                  <div
                    v-for="(source, sIdx) in (nodeConfig.finish_data_sources || [])"
                    :key="sIdx"
                    class="data-source-item"
                  >
                    <div class="source-header">
                      <span>数据源 {{ sIdx + 1 }}</span>
                      <el-button type="danger" size="small" link @click="removeFinishDataSource(sIdx)">删除</el-button>
                    </div>
                    <div class="source-content">
                      <el-select
                        v-model="source.template_id"
                        placeholder="选择表单模板"
                        size="small"
                        style="width:100%; margin-bottom:6px"
                      >
                        <el-option
                          v-for="template in templates"
                          :key="template.id"
                          :label="`${template.name} (ID: ${template.id})`"
                          :value="template.id"
                        />
                      </el-select>
                      <el-input
                        v-model="source.alias"
                        placeholder="别名（可选，如 source1）"
                        size="small"
                      />
                    </div>
                  </div>
                  <el-button size="small" type="primary" plain @click="addFinishDataSource" style="margin-bottom:12px">
                    + 添加表单
                  </el-button>

                  <!-- 条件组 -->
                  <el-divider content-position="left" style="margin-top:0">
                    <span class="divider-title" style="font-size:13px">判断条件</span>
                  </el-divider>
                  <div class="form-tip" style="margin-bottom:8px;">条件组之间是"或"关系，组内条件是"且"关系，满足任一条件组则填报节点结束</div>

                  <div class="condition-groups">
                    <div
                      v-for="(group, gIdx) in (nodeConfig.finish_condition_groups || [])"
                      :key="gIdx"
                      class="condition-group"
                    >
                      <div class="group-header">
                        <el-tag type="warning" size="small">条件组 {{ gIdx + 1 }}</el-tag>
                        <span class="or-label" v-if="gIdx < (nodeConfig.finish_condition_groups || []).length - 1">OR</span>
                        <el-button type="danger" size="small" link @click="removeFinishConditionGroup(gIdx)">删除条件组</el-button>
                      </div>

                      <div v-for="(cond, cIdx) in group.conditions" :key="cIdx" class="cond-row">
                        <el-select v-model="cond.type" placeholder="条件类型" size="small" style="width:100px">
                          <el-option label="字段判断" value="field" />
                          <el-option label="公式判断" value="formula" />
                        </el-select>

                        <!-- 字段判断 -->
                        <template v-if="cond.type === 'field'">
                          <el-select v-model="cond.field" placeholder="选择字段" size="small" style="width:120px; margin:0 4px">
                            <el-option-group label="本条数据">
                              <el-option
                                v-for="f in getTemplateFields(nodeConfig.form_template_id)"
                                :key="f.name"
                                :label="f.label || f.name"
                                :value="`current.${f.name}`"
                              />
                            </el-option-group>
                            <el-option-group
                              v-for="(src, si) in (nodeConfig.finish_data_sources || [])"
                              :key="si"
                              :label="src.alias || `数据源${si + 1}`"
                            >
                              <el-option
                                v-for="f in getTemplateFields(src.template_id)"
                                :key="f.name"
                                :label="f.label || f.name"
                                :value="`${src.alias || 'source' + (si + 1)}.${f.name}`"
                              />
                            </el-option-group>
                          </el-select>
                          <el-select v-model="cond.operator" placeholder="运算符" size="small" style="width:90px; margin-right:4px">
                            <el-option label="等于" value="eq" />
                            <el-option label="不等于" value="ne" />
                            <el-option label="大于" value="gt" />
                            <el-option label="大于等于" value="gte" />
                            <el-option label="小于" value="lt" />
                            <el-option label="小于等于" value="lte" />
                            <el-option label="包含" value="contains" />
                            <el-option label="不包含" value="not_contains" />
                            <el-option label="为空" value="is_null" />
                            <el-option label="不为空" value="not_null" />
                          </el-select>
                          <el-input v-model="cond.value" placeholder="值" size="small" style="width:100px" />
                        </template>

                        <!-- 公式判断 -->
                        <template v-else-if="cond.type === 'formula'">
                          <el-input
                            v-model="cond.formula"
                            placeholder="如: {{current.count}} >= 3"
                            size="small"
                            style="flex:1; margin-left:4px"
                          />
                        </template>

                        <el-button type="danger" size="small" link style="margin-left:4px" @click="removeFinishCondition(gIdx, cIdx)">删除</el-button>
                      </div>

                      <div style="margin-top:6px">
                        <el-button size="small" @click="addFinishCondition(gIdx)">+ 添加条件（AND）</el-button>
                      </div>
                    </div>
                  </div>

                  <el-button type="primary" size="small" @click="addFinishConditionGroup" style="margin-top:8px">
                    + 添加条件组（OR）
                  </el-button>
                </template>
              </el-form>
            </el-tab-pane>

            <!-- 表单权限配置 -->
            <el-tab-pane label="表单权限" name="form_permissions" v-if="nodeConfig.form_template_id && ['approval', 'task', 'cc', 'data_fill'].includes(selectedNodeData.type)">
              <div class="permission-container">
                <div class="permission-header">
                  <span>字段权限控制</span>
                  <el-button type="primary" size="small" @click="setAllPermissions('editable')">全部可编辑</el-button>
                  <el-button size="small" @click="setAllPermissions('visible')">全部仅可见</el-button>
                  <el-button type="danger" size="small" @click="setAllPermissions('hidden')">全部隐藏</el-button>
                </div>
                <el-table :data="getTemplateFields(nodeConfig.form_template_id)" border style="width: 100%">
                  <el-table-column prop="label" label="字段名称" width="150" />
                  <el-table-column prop="type" label="字段类型" width="100" />
                  <el-table-column label="权限" width="200">
                    <template #default="{ row }">
                      <el-select 
                        v-model="nodeConfig.field_permissions[row.name]" 
                        size="small"
                        style="width: 100%"
                      >
                        <el-option label="可编辑" value="editable" />
                        <el-option label="仅可见" value="visible" />
                        <el-option label="隐藏" value="hidden" />
                      </el-select>
                    </template>
                  </el-table-column>
                  <el-table-column label="说明" min-width="150">
                    <template #default="{ row }">
                      <span v-if="nodeConfig.field_permissions[row.name] === 'editable'">用户可查看和修改此字段</span>
                      <span v-else-if="nodeConfig.field_permissions[row.name] === 'visible'">用户只能查看，不能修改</span>
                      <span v-else>用户无法看到此字段</span>
                    </template>
                  </el-table-column>
                </el-table>
                <div class="permission-tip">
                  <p>📌 <strong>权限说明：</strong></p>
                  <p>• <strong>可编辑</strong>：用户可查看和修改此字段</p>
                  <p>• <strong>仅可见</strong>：用户只能查看，不能修改（适用于审批时查看原始数据）</p>
                  <p>• <strong>隐藏</strong>：用户无法看到此字段（适用于敏感信息）</p>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 条件节点配置 - 斑斑低代码平台标准 -->
            <el-tab-pane label="条件配置" name="condition" v-if="selectedNodeData.type === 'condition' || selectedNodeData.type === 'parallel'">
              <el-form label-width="120px" class="node-config-form">
                <!-- 分支优先级（仅条件分支） -->
                <template v-if="selectedNodeData.type === 'condition'">
                  <el-form-item label="分支优先级">
                    <el-input-number v-model="nodeConfig.priority" :min="1" :max="100" :step="1" style="width:120px" />
                    <div class="form-tip">优先级越小越先判断（从左到右：1、2、3…），不满足所有条件则进入"其他分支"</div>
                  </el-form-item>
                </template>
                
                <!-- 数据源表单 -->
                <el-divider content-position="left">
                  <span class="divider-title">数据源表单</span>
                </el-divider>
                <div class="form-tip" style="margin-bottom:8px;">默认使用当前表单数据，可添加其他表单作为判断条件的数据来源</div>
                <div v-for="(source, index) in nodeConfig.data_sources" :key="index" class="data-source-item">
                  <div class="source-header">
                    <span>数据源 {{ index + 1 }}</span>
                    <el-button type="danger" size="small" link @click="removeDataSource(index)">删除</el-button>
                  </div>
                  <div class="source-content">
                    <el-select
                      v-model="source.template_id"
                      placeholder="选择表单模板"
                      style="width: 100%; margin-bottom: 8px;"
                      @change="updateDataSourceFilters(index)"
                    >
                      <el-option
                        v-for="template in templates"
                        :key="template.id"
                        :label="`${template.name} (ID: ${template.id})`"
                        :value="template.id"
                      />
                    </el-select>
                    <el-input
                      v-model="source.alias"
                      placeholder="别名（可选，如 source1）"
                      size="small"
                      style="margin-bottom: 8px;"
                    />
                    <div class="filter-conditions">
                      <div v-for="(filter, filterIndex) in source.filter_conditions" :key="filterIndex" class="filter-item">
                        <el-select v-model="filter.field" placeholder="字段" size="small" style="width: 120px;">
                          <el-option
                            v-for="field in getTemplateFields(source.template_id)"
                            :key="field.name"
                            :label="field.label"
                            :value="field.name"
                          />
                        </el-select>
                        <el-select v-model="filter.operator" placeholder="操作符" size="small" style="width: 100px; margin: 0 8px;">
                          <el-option label="等于" value="eq" />
                          <el-option label="不等于" value="ne" />
                          <el-option label="大于" value="gt" />
                          <el-option label="小于" value="lt" />
                          <el-option label="包含" value="contains" />
                          <el-option label="不包含" value="not_contains" />
                          <el-option label="为空" value="is_null" />
                          <el-option label="不为空" value="not_null" />
                        </el-select>
                        <el-input v-model="filter.value" placeholder="值" size="small" style="width: 100px;" />
                        <el-button type="danger" size="small" link @click="removeFilterCondition(index, filterIndex)">删除</el-button>
                      </div>
                      <div v-if="(source.filter_conditions || []).length > 1" style="margin:4px 0">
                        <el-select v-model="source.filter_logic" size="small" style="width:160px">
                          <el-option label="满足所有条件(AND)" value="and" />
                          <el-option label="满足任一条件(OR)" value="or" />
                        </el-select>
                      </div>
                      <el-button size="small" @click="addFilterCondition(index)">添加筛选条件</el-button>
                    </div>
                  </div>
                </div>
                <el-button type="primary" size="small" @click="addDataSource" style="margin-bottom:12px">+ 添加数据源表单</el-button>
                
                <!-- 分支判断条件（条件组） -->
                <el-divider content-position="left">
                  <span class="divider-title">分支判断条件</span>
                </el-divider>
                <div class="form-tip" style="margin-bottom:8px;">
                  条件组之间是"或"关系，组内条件是"且"关系。满足任一条件组则进入该分支
                </div>
                
                <!-- 条件组列表 -->
                <div class="condition-groups">
                  <div 
                    v-for="(group, gIdx) in (nodeConfig.condition_groups || [])" 
                    :key="gIdx"
                    class="condition-group"
                  >
                    <div class="group-header">
                      <el-tag type="warning" size="small">条件组 {{ gIdx + 1 }}</el-tag>
                      <span class="or-label" v-if="gIdx < (nodeConfig.condition_groups || []).length - 1">OR</span>
                      <el-button type="danger" size="small" link @click="removeConditionGroup(gIdx)">删除条件组</el-button>
                    </div>
                    
                    <div v-for="(cond, cIdx) in group.conditions" :key="cIdx" class="cond-row">
                      <el-select v-model="cond.type" placeholder="条件类型" size="small" style="width:100px">
                        <el-option label="字段判断" value="field" />
                        <el-option label="公式判断" value="formula" />
                        <el-option label="触发类型" value="trigger_type" />
                      </el-select>
                      
                      <!-- 字段判断 -->
                      <template v-if="cond.type === 'field'">
                        <el-select v-model="cond.field" placeholder="选择字段" size="small" style="width:120px; margin:0 4px">
                          <el-option-group label="当前表单">
                            <el-option
                              v-for="f in getTemplateFields(nodeConfig.form_template_id)"
                              :key="f.name"
                              :label="f.label || f.name"
                              :value="`current.${f.name}`"
                            />
                          </el-option-group>
                          <el-option-group v-for="(src, si) in (nodeConfig.data_sources||[])" :key="si" :label="src.alias || `数据源${si+1}`">
                            <el-option
                              v-for="f in getTemplateFields(src.template_id)"
                              :key="f.name"
                              :label="f.label || f.name"
                              :value="`${src.alias || 'source'+(si+1)}.${f.name}`"
                            />
                          </el-option-group>
                        </el-select>
                        <el-select v-model="cond.operator" placeholder="运算符" size="small" style="width:80px; margin-right:4px">
                          <el-option label="等于" value="eq" />
                          <el-option label="不等于" value="ne" />
                          <el-option label="大于" value="gt" />
                          <el-option label="大于等于" value="gte" />
                          <el-option label="小于" value="lt" />
                          <el-option label="小于等于" value="lte" />
                          <el-option label="包含" value="contains" />
                          <el-option label="不包含" value="not_contains" />
                          <el-option label="为空" value="is_null" />
                          <el-option label="不为空" value="not_null" />
                        </el-select>
                        <el-input v-model="cond.value" placeholder="值" size="small" style="width:100px" />
                      </template>
                      
                      <!-- 公式判断 -->
                      <template v-else-if="cond.type === 'formula'">
                        <el-input v-model="cond.formula" placeholder="如: {{current.amount}} > 1000" size="small" style="flex:1; margin-left:4px" />
                      </template>
                      
                      <!-- 触发类型判断 -->
                      <template v-else-if="cond.type === 'trigger_type'">
                        <el-checkbox-group v-model="cond.trigger_types" size="small" style="margin-left:4px">
                          <el-checkbox value="create" label="新增" />
                          <el-checkbox value="update" label="修改" />
                          <el-checkbox value="delete" label="删除" />
                        </el-checkbox-group>
                      </template>
                      
                      <el-button type="danger" size="small" link style="margin-left:4px" @click="removeCondition(gIdx, cIdx)">删除</el-button>
                    </div>
                    
                    <div style="margin-top:6px">
                      <el-button size="small" @click="addCondition(gIdx)">+ 添加条件（AND）</el-button>
                    </div>
                  </div>
                </div>
                
                <el-button type="primary" size="small" @click="addConditionGroup" style="margin-top:8px">
                  + 添加条件组（OR）
                </el-button>
              </el-form>
            </el-tab-pane>
            
            <!-- 数据变化节点配置（触发节点） -->
            <el-tab-pane label="触发配置" name="data_change_trigger" v-if="selectedNodeData.type === 'trigger' || selectedNodeData.type === 'data_change'">
              <el-form label-width="120px" class="node-config-form">
                <el-form-item label="触发类型" v-if="selectedNodeData.type === 'trigger'">
                  <el-radio-group v-model="nodeConfig.trigger_type">
                    <el-radio-button value="data_change">数据变化</el-radio-button>
                    <el-radio-button value="timer">定时触发</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                
                <!-- 数据变化配置 -->
                <template v-if="selectedNodeData.type === 'data_change' || nodeConfig.trigger_type === 'data_change'">
                  <el-divider content-position="left">
                    <span class="divider-title">变化类型</span>
                  </el-divider>
                  <el-form-item label="监听变化类型">
                    <el-checkbox-group v-model="nodeConfig.change_types">
                      <el-checkbox value="create" label="新增数据" />
                      <el-checkbox value="update" label="修改数据" />
                      <el-checkbox value="delete" label="删除数据" />
                    </el-checkbox-group>
                    <div class="form-tip">同时勾选多个：任一变化发生即触发流程</div>
                  </el-form-item>
                </template>
                
                <!-- 定时触发配置 -->
                <template v-if="nodeConfig.trigger_type === 'timer'">
                  <el-form-item label="Cron表达式">
                    <el-input v-model="nodeConfig.cron_expression" placeholder="如: 0 9 * * 1-5" />
                    <div class="form-tip">示例：每天9点 "0 9 * * *"，每周一9点 "0 9 * * 1"</div>
                  </el-form-item>
                </template>
                
                <!-- 表单权限（数据变化节点专用） -->
                <template v-if="nodeConfig.form_template_id && (selectedNodeData.type === 'trigger' || selectedNodeData.type === 'data_change')">
                  <el-divider content-position="left">
                    <span class="divider-title">表单字段权限</span>
                  </el-divider>
                  <div class="form-tip" style="margin: 0 0 12px 0; padding: 8px 12px; background:#f0f9ff; border-radius:4px;">
                    📌 数据变化节点的字段权限对应提交/编辑表单时的字段可见和可编辑状态
                  </div>
                  <div class="permission-header" style="margin-bottom:8px;">
                    <el-button-group>
                      <el-button size="small" type="primary" @click="setAllPermissions('editable')">全部可编辑</el-button>
                      <el-button size="small" @click="setAllPermissions('visible')">全部仅可见</el-button>
                      <el-button size="small" type="danger" plain @click="setAllPermissions('hidden')">全部隐藏</el-button>
                    </el-button-group>
                  </div>
                  <el-table :data="getTemplateFields(nodeConfig.form_template_id)" border size="small">
                    <el-table-column prop="label" label="字段名" width="120" />
                    <el-table-column prop="type" label="类型" width="80" />
                    <el-table-column label="权限">
                      <template #default="{ row }">
                        <el-select 
                          v-model="nodeConfig.field_permissions[row.name]" 
                          size="small"
                          style="width: 100%"
                        >
                          <el-option label="可编辑" value="editable" />
                          <el-option label="仅可见" value="visible" />
                          <el-option label="隐藏" value="hidden" />
                        </el-select>
                      </template>
                    </el-table-column>
                  </el-table>
                </template>
                <div v-else-if="selectedNodeData.type === 'trigger' || selectedNodeData.type === 'data_change'" 
                     class="form-tip" style="margin-top:12px;">
                  💡 请先在"基本属性"中绑定表单模板，以配置字段权限
                </div>
              </el-form>
            </el-tab-pane>
            
            <!-- 插件节点配置 -->
            <el-tab-pane label="插件配置" name="plugin_trigger" v-if="selectedNodeData.type === 'trigger'">
              <el-form label-width="100px">
                <el-form-item label="插件ID">
                  <el-input v-model="nodeConfig.plugin_id" placeholder="输入插件ID" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 跨表数据操作节点配置（添加/修改/删除数据节点） -->
            <el-tab-pane label="数据操作" name="cross_data_op" v-if="['add_data', 'update_data', 'delete_data'].includes(selectedNodeData.type)">
              <el-form label-width="100px" class="node-config-form">
                <el-form-item label="目标表单">
                  <el-select
                    v-model="nodeConfig.target_template_id"
                    placeholder="选择目标表单"
                    filterable
                    style="width:100%"
                    @change="handleTargetTemplateChange"
                  >
                    <el-option
                      v-for="template in templates"
                      :key="template.id"
                      :label="`${template.name} (ID: ${template.id})`"
                      :value="template.id"
                    />
                  </el-select>
                  <div class="form-tip">选择要{{ selectedNodeData.type === 'add_data' ? '添加数据到' : selectedNodeData.type === 'update_data' ? '修改数据的' : '删除数据的' }}目标表单</div>
                </el-form-item>
                
                <!-- 筛选条件（修改/删除数据需要） -->
                <template v-if="nodeConfig.target_template_id && ['update_data', 'delete_data'].includes(selectedNodeData.type)">
                  <el-divider content-position="left">
                    <span class="divider-title">目标数据筛选条件</span>
                  </el-divider>
                  <div class="form-tip" style="margin-bottom:8px;">设置筛选条件，确定要{{ selectedNodeData.type === 'update_data' ? '修改' : '删除' }}哪些数据</div>
                  <div class="condition-list">
                    <div v-for="(cond, idx) in (nodeConfig.filter_conditions || [])" :key="idx" class="condition-row">
                      <el-select v-model="cond.field" placeholder="目标字段" size="small" style="width:120px">
                        <el-option
                          v-for="field in getTemplateFields(nodeConfig.target_template_id)"
                          :key="field.name"
                          :label="field.label || field.name"
                          :value="field.name"
                        />
                      </el-select>
                      <el-select v-model="cond.operator" placeholder="条件" size="small" style="width:100px; margin:0 6px">
                        <el-option label="等于" value="eq" />
                        <el-option label="不等于" value="ne" />
                        <el-option label="包含" value="contains" />
                        <el-option label="不包含" value="not_contains" />
                        <el-option label="为空" value="is_null" />
                        <el-option label="不为空" value="not_null" />
                      </el-select>
                      <el-select v-model="cond.value_type" size="small" style="width:80px; margin-right:6px">
                        <el-option label="字段值" value="field" />
                        <el-option label="固定值" value="fixed" />
                      </el-select>
                      <el-select v-if="cond.value_type === 'field'" v-model="cond.value" placeholder="当前表单字段" size="small" style="width:120px">
                        <el-option
                          v-for="field in getTemplateFields(nodeConfig.form_template_id)"
                          :key="field.name"
                          :label="field.label || field.name"
                          :value="`{{current.${field.name}}}`"
                        />
                      </el-select>
                      <el-input v-else v-model="cond.value" placeholder="值" size="small" style="width:120px" />
                      <el-button type="danger" size="small" link style="margin-left:6px" @click="removeTargetFilterCondition(idx)">删除</el-button>
                    </div>
                    <div style="margin-top:8px">
                      <el-select v-if="(nodeConfig.filter_conditions || []).length > 1" v-model="nodeConfig.filter_logic" size="small" style="width:120px; margin-right:8px">
                        <el-option label="满足所有条件(AND)" value="and" />
                        <el-option label="满足任一条件(OR)" value="or" />
                      </el-select>
                      <el-button size="small" @click="addTargetFilterCondition">+ 添加筛选条件</el-button>
                    </div>
                  </div>
                </template>
                
                <!-- 数据源表单 -->
                <el-divider content-position="left" v-if="nodeConfig.target_template_id && selectedNodeData.type !== 'delete_data'">
                  <span class="divider-title">数据源表单</span>
                </el-divider>
                <template v-if="nodeConfig.target_template_id && selectedNodeData.type !== 'delete_data'">
                  <div class="form-tip" style="margin-bottom:8px;">默认使用当前表单数据，可添加其他表单数据源</div>
                  <div v-for="(source, sIdx) in (nodeConfig.data_sources || [])" :key="sIdx" class="data-source-item">
                    <div class="source-header">
                      <span>数据源 {{ sIdx + 1 }}</span>
                      <el-button type="danger" size="small" link @click="removeDataSource(sIdx)">删除</el-button>
                    </div>
                    <el-select v-model="source.template_id" placeholder="选择表单" size="small" style="width:100%; margin-bottom:6px" @change="updateDataSourceFilters(sIdx)">
                      <el-option v-for="t in templates" :key="t.id" :label="`${t.name}(ID:${t.id})`" :value="t.id" />
                    </el-select>
                    <el-input v-model="source.alias" placeholder="别名（可选，如 source1）" size="small" style="margin-bottom:6px" />
                  </div>
                  <el-button size="small" @click="addDataSource">+ 添加数据源表单</el-button>
                </template>
                
                <!-- 字段映射（添加/修改） -->
                <template v-if="nodeConfig.target_template_id && selectedNodeData.type !== 'delete_data'">
                  <el-divider content-position="left">
                    <span class="divider-title">{{ selectedNodeData.type === 'add_data' ? '设置目标表单字段值' : '修改字段值' }}</span>
                  </el-divider>
                  <div class="form-tip" style="margin-bottom:8px;">
                    为目标表单的字段设置值来源
                  </div>
                  <div class="field-mapping-table">
                    <div class="mapping-header">
                      <span style="width:140px">目标字段</span>
                      <span style="flex:1">赋值方式</span>
                      <span style="width:160px">值</span>
                    </div>
                    <div 
                      v-for="field in getTemplateFields(nodeConfig.target_template_id)" 
                      :key="field.name" 
                      class="mapping-row"
                    >
                      <span class="field-name" style="width:140px">
                        <el-tag size="small" type="info">{{ field.type }}</el-tag>
                        {{ field.label || field.name }}
                      </span>
                      <el-select 
                        v-model="getFieldMapping(field.name).type" 
                        size="small" 
                        style="width:110px; margin:0 6px"
                        @change="onFieldMappingTypeChange(field.name, $event)"
                      >
                        <el-option label="不赋值" value="none" />
                        <el-option label="来自字段" value="field" />
                        <el-option label="自定义值" value="fixed" />
                        <el-option label="公式编辑" value="formula" />
                      </el-select>
                      <template v-if="getFieldMapping(field.name).type === 'field'">
                        <el-select v-model="getFieldMapping(field.name).value" placeholder="选择数据源字段" size="small" style="flex:1">
                          <el-option-group label="当前表单">
                            <el-option
                              v-for="sf in getTemplateFields(nodeConfig.form_template_id)"
                              :key="sf.name"
                              :label="sf.label || sf.name"
                              :value="`{{current.${sf.name}}}`"
                            />
                          </el-option-group>
                          <el-option-group v-for="(src, si) in (nodeConfig.data_sources||[])" :key="si" :label="`${src.alias || '数据源' + (si+1)}`">
                            <el-option
                              v-for="sf in getTemplateFields(src.template_id)"
                              :key="sf.name"
                              :label="sf.label || sf.name"
                              :value="`{{${src.alias || 'source'+(si+1)}.${sf.name}}}`"
                            />
                          </el-option-group>
                        </el-select>
                      </template>
                      <template v-else-if="getFieldMapping(field.name).type === 'fixed'">
                        <el-input v-model="getFieldMapping(field.name).value" placeholder="输入固定值" size="small" style="flex:1" />
                      </template>
                      <template v-else-if="getFieldMapping(field.name).type === 'formula'">
                        <el-input v-model="getFieldMapping(field.name).value" placeholder="如: {{current.qty}} + {{current.add_qty}}" size="small" style="flex:1" />
                      </template>
                      <template v-else>
                        <span style="flex:1; color:#999; font-size:12px; padding-left:8px">不修改，保留原值</span>
                      </template>
                    </div>
                  </div>
                </template>
              </el-form>
            </el-tab-pane>
            
            <!-- 延迟节点配置 -->
            <el-tab-pane label="延迟配置" name="delay" v-if="selectedNodeData.type === 'delay'">
              <el-form label-width="100px">
                <el-form-item label="延迟时间(秒)">
                  <el-input-number v-model="nodeConfig.delay_seconds" :min="0" :step="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 子流程配置 -->
            <el-tab-pane label="子流程" name="subprocess" v-if="selectedNodeData.type === 'sub_process'">
              <el-form label-width="100px">
                <el-form-item label="子流程ID">
                  <el-input-number v-model="nodeConfig.sub_workflow_id" :min="1" :step="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 插件配置（通用） -->
            <el-tab-pane label="插件" name="plugins" v-if="['approval', 'task', 'data_change', 'trigger'].includes(selectedNodeData.type)">
              <el-form label-width="100px">
                <el-form-item label="前置插件">
                  <el-input v-model="nodeConfig.plugins.before" placeholder="插件ID" />
                </el-form-item>
                <el-form-item label="后置插件">
                  <el-input v-model="nodeConfig.plugins.after" placeholder="插件ID" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
          
          <el-divider />
          
          <div class="property-actions">
            <el-button type="danger" @click="deleteNode">删除节点</el-button>
            <el-button type="primary" @click="saveNodeConfig">保存配置</el-button>
          </div>
        </div>
        <div v-else class="empty-properties">
          <el-empty description="请选择节点进行配置" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check, CircleCheck, View, UserFilled, Document, Message, Edit,
  Connection, Share, Sort, SetUp, MagicStick, Refresh, Timer, VideoPlay,
  Plus, Delete
} from '@element-plus/icons-vue'
import { templateAPI, userAPI, workflowAPI } from '../../common/api'

interface WorkflowNode {
  id: string
  type: string
  name: string
  description?: string
  x: number
  y: number
  config?: {
    // 通用配置
    form_template_id?: number
    field_permissions?: Record<string, 'visible' | 'editable' | 'hidden'>
    
    // 触发节点配置
    trigger_type?: 'data_change' | 'timer'
    change_types?: ('create' | 'update' | 'delete')[]
    cron_expression?: string
    
    // 审批/办理/抄送节点配置
    approval_type?: 'auto_approve' | 'auto_reject' | 'manual'
    approval_mode?: 'regular' | 'hierarchical'
    hierarchical_order?: 'bottom_up' | 'top_down'
    assignee_source?: 'submitter' | 'specified' | 'department_manager' | 'form_member_field' | 'form_department_field'
    assignee_ids?: string[]          // 指定成员时：['user:1', 'role:2']
    assignee_field?: string          // 表单字段时：字段名
    assignee_value?: string | number | number[]  // 旧字段兼容
    manager_order?: 'bottom_up' | 'top_down'
    manager_level?: 'direct' | 'level2' | 'level3' | 'top'
    multi_person_mode?: 'all' | 'any' | 'sequential'
    
    // 审批人为空时处理
    empty_assignee_action?: 'auto_approve' | 'specified_fallback' | 'admin_fallback'
    fallback_assignee_id?: number
    
    // 审批人与提交人相同时处理
    same_person_action?: 'self_approve' | 'to_department_manager' | 'auto_skip'
    
    // 操作权限
    allow_transfer?: boolean
    require_comment?: boolean
    
    // 退回配置（审批节点）
    allow_reject_back?: boolean
    reject_back_range?: 'any' | 'limited'
    reject_back_node_id?: string
    
    // 超时配置
    timeout_hours?: number
    timeout_action?: 'notify' | 'auto_approve' | 'auto_reject'
    
    // 条件节点配置
    priority?: number
    expression?: string
    condition_groups?: Array<{
      conditions: Array<{
        type: 'field' | 'formula' | 'trigger_type'
        field?: string
        operator?: string
        value?: string
        formula?: string
        trigger_types?: ('create' | 'update' | 'delete')[]
      }>
    }>
    
    // 数据操作节点配置
    operation_type?: 'create' | 'update' | 'delete'
    target_template_id?: number
    data_mapping?: Record<string, string>
    field_mappings?: Record<string, { type: 'none' | 'field' | 'fixed' | 'formula', value: string }>
    filter_conditions?: Array<{
      field: string
      operator: string
      value_type: 'field' | 'fixed'
      value: string
    }>
    filter_logic?: 'and' | 'or'
    
    // 数据源配置
    data_sources?: Array<{
      template_id: number
      alias?: string
      filter_conditions?: any[]
      filter_logic?: 'and' | 'or'
    }>
    
    // 延迟节点配置
    delay_seconds?: number
    
    // 子流程配置
    sub_workflow_id?: number
    
    // 插件配置
    plugin_id?: string
    plugins?: {
      before?: string
      after?: string
    }
    
    // 数据填报节点：填报结束条件
    enable_finish_condition?: boolean
    finish_data_sources?: Array<{
      template_id: number | null
      alias?: string
    }>
    finish_condition_groups?: Array<{
      conditions: Array<{
        type: 'field' | 'formula'
        field?: string
        operator?: string
        value?: string
        formula?: string
      }>
    }>
  }
}

interface Connection {
  id: string
  from: string
  to: string
  path: string
  label?: string  // 条件表达式
}

const route = useRoute()
const router = useRouter()
const workflowId = route.params.id as string
const workflowName = ref('新建流程')

// 模板列表 - 用于绑定表单
const templates = ref<any[]>([])
const loadingTemplates = ref(false)

// 用户列表 - 用于人员选择
const users = ref<any[]>([])
const loadingUsers = ref(false)

// 角色列表 - 用于人员选择
const roles = ref<any[]>([])
const loadingRoles = ref(false)

const canvasRef = ref<HTMLElement>()
const connectionsSvg = ref<SVGSVGElement>()

// 节点类型 - 根据斑斑低代码平台支持的节点类型
const nodeTypes = [
  { type: 'start', name: '开始节点', icon: 'VideoPlay', color: '#67C23A' },
  { type: 'end', name: '结束节点', icon: 'CircleCheck', color: '#F56C6C' },
  { type: 'trigger', name: '触发节点', icon: 'MagicStick', color: '#8A2BE2' },
  { type: 'approval', name: '审批节点', icon: 'UserFilled', color: '#409EFF' },
  { type: 'task', name: '办理节点', icon: 'Document', color: '#E6A23C' },
  { type: 'cc', name: '抄送节点', icon: 'Message', color: '#909399' },
  { type: 'data_fill', name: '数据填报', icon: 'Edit', color: '#8A2BE2' },
  { type: 'condition', name: '条件分支', icon: 'Connection', color: '#67C23A' },
  { type: 'parallel', name: '并行分支', icon: 'Share', color: '#E6A23C' },
  { type: 'add_data', name: '添加数据', icon: 'Plus', color: '#67C23A' },
  { type: 'update_data', name: '修改数据', icon: 'Edit', color: '#409EFF' },
  { type: 'delete_data', name: '删除数据', icon: 'Delete', color: '#F56C6C' },
  { type: 'sub_process', name: '子流程', icon: 'SetUp', color: '#409EFF' },
  { type: 'delay', name: '延迟节点', icon: 'Timer', color: '#909399' }
]

// 加载模板列表
const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await templateAPI.list({ limit: 100 })
    if (res && Array.isArray(res)) {
      templates.value = res
    } else if (res?.data && Array.isArray(res.data)) {
      templates.value = res.data
    }
  } catch (error) {
    console.error('加载模板失败:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loadingTemplates.value = false
  }
}

// 加载用户列表
const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const res = await userAPI.list({ limit: 200 })
    // 后端返回 BaseResponse: { code, message, data: { total, users: [...] } }
    // 前端拦截器直接返回 response.data，所以 res = { code, message, data: { total, users } }
    if (res?.data?.users && Array.isArray(res.data.users)) {
      users.value = res.data.users
    } else if (res?.data && Array.isArray(res.data)) {
      users.value = res.data
    } else if (Array.isArray(res)) {
      users.value = res
    } else {
      users.value = []
      console.warn('用户列表数据格式不符合预期:', res)
    }
  } catch (error) {
    console.error('加载用户失败:', error)
    // 非致命错误，不弹出错误消息，使用空列表
    users.value = []
  } finally {
    loadingUsers.value = false
  }
}

// 加载角色列表（TODO: 需要角色API）
const loadRoles = async () => {
  loadingRoles.value = true
  try {
    // 暂时使用模拟数据
    roles.value = [
      { id: 1, name: '管理员', code: 'admin' },
      { id: 2, name: '普通用户', code: 'user' },
      { id: 3, name: '部门经理', code: 'manager' },
      { id: 4, name: '人事专员', code: 'hr' }
    ]
  } catch (error) {
    console.error('加载角色失败:', error)
  } finally {
    loadingRoles.value = false
  }
}

// 初始化加载数据
const initData = async () => {
  loadTemplates()
  loadUsers()
  loadRoles()
  
  // 如果提供了工作流ID，则加载现有工作流
  if (workflowId && workflowId !== 'new') {
    await loadWorkflow(parseInt(workflowId))
  }
}

// 加载现有工作流
const loadWorkflow = async (id: number) => {
  try {
    const response = await workflowAPI.get(id)
    const workflow = response
    
    workflowName.value = workflow.name
    
    // 加载节点数据
    if (workflow.nodes && Array.isArray(workflow.nodes)) {
      nodes.value = workflow.nodes.map((node: any) => ({
        id: node.id,
        type: node.type,
        name: node.name,
        x: 100, // 默认位置，实际应该从node_definitions或config中获取
        y: 200,
        description: node.description || '',
        config: node.config || {}
      }))
    }
    
    // 加载连线数据
    if (workflow.edges && Array.isArray(workflow.edges)) {
      connections.value = workflow.edges.map((edge: any) => ({
        id: edge.id || `conn-${edge.source}-${edge.target}`,
        from: edge.source,
        to: edge.target,
        path: '', // 路径会在updateConnections中生成
        label: edge.label || ''
      }))
      updateConnections()
    }
    
    // 如果有node_definitions，可以更新节点配置
    if (workflow.node_definitions && Array.isArray(workflow.node_definitions)) {
      workflow.node_definitions.forEach((nodeDef: any) => {
        const node = nodes.value.find(n => n.id === nodeDef.id)
        if (node && nodeDef.config) {
          node.config = { ...node.config, ...nodeDef.config }
        }
      })
    }
    
    ElMessage.success('工作流加载成功')
  } catch (error: any) {
    console.error('加载工作流失败:', error)
    ElMessage.error(`加载失败: ${error.message || '未知错误'}`)
  }
}

// 节点数据
const nodes = ref<WorkflowNode[]>([
  { id: 'start-1', type: 'start', name: '开始', x: 100, y: 200, description: '流程开始' }
])

// 连接线数据
const connections = ref<Connection[]>([])

// 选中状态
const selectedNode = ref<string | null>(null)
const selectedConnection = ref<string | null>(null)

// 拖拽状态
const isDragging = ref(false)
const dragNode = ref<WorkflowNode | null>(null)
const dragOffset = ref({ x: 0, y: 0 })

// 连线状态
const isConnecting = ref(false)
const connectionStart = ref<{ nodeId: string; type: string } | null>(null)
const previewPath = ref('')
const mousePosition = ref({ x: 0, y: 0 })

// 计算选中的节点数据
const selectedNodeData = computed(() => {
  if (!selectedNode.value) return null
  return nodes.value.find(n => n.id === selectedNode.value) || null
})

// 确保节点配置存在
const nodeConfig = computed(() => {
  if (!selectedNodeData.value) return {}
  if (!selectedNodeData.value.config) {
    selectedNodeData.value.config = {}
  }
  // 确保 plugins 对象存在
  if (!selectedNodeData.value.config.plugins) {
    selectedNodeData.value.config.plugins = { before: '', after: '' }
  }
  return selectedNodeData.value.config
})

// 属性面板活动标签
const activePropertyTab = ref('basic')

// 辅助函数
const getAssigneePlaceholder = (type: string) => {
  const placeholders: Record<string, string> = {
    user: '用户ID',
    role: '角色ID',
    expression: '如: {{applicant.manager_id}}',
    form_field: '表单字段名'
  }
  return placeholders[type] || '请输入'
}

// 获取模板字段
const getTemplateFields = (templateId?: number) => {
  if (!templateId) return []
  const template = templates.value.find(t => t.id === templateId)
  if (!template || !template.modules) return []
  
  const fields: Array<{name: string, label: string, type: string}> = []
  template.modules.forEach((module: any) => {
    if (module.fields && Array.isArray(module.fields)) {
      module.fields.forEach((field: any) => {
        fields.push({
          name: field.name || field.field,
          label: field.label || field.name || field.field,
          type: field.type || 'text'
        })
      })
    }
  })
  return fields
}

// 处理模板变更
const handleTemplateChange = (templateId?: number) => {
  if (!templateId) {
    // 清空字段权限
    if (nodeConfig.value.field_permissions) {
      nodeConfig.value.field_permissions = {}
    }
    return
  }
  
  // 初始化字段权限
  const fields = getTemplateFields(templateId)
  if (!nodeConfig.value.field_permissions) {
    nodeConfig.value.field_permissions = {}
  }
  
  // 为新增字段设置默认权限（可见且可编辑）
  fields.forEach(field => {
    if (!nodeConfig.value.field_permissions![field.name]) {
      nodeConfig.value.field_permissions![field.name] = 'editable'
    }
  })
}

// 设置所有字段权限
const setAllPermissions = (permission: 'editable' | 'visible' | 'hidden') => {
  if (!nodeConfig.value.field_permissions) {
    nodeConfig.value.field_permissions = {}
  }
  
  const fields = getTemplateFields(nodeConfig.value.form_template_id)
  fields.forEach(field => {
    nodeConfig.value.field_permissions![field.name] = permission
  })
  
  ElMessage.success(`已设置所有字段为${permission === 'editable' ? '可编辑' : permission === 'visible' ? '仅可见' : '隐藏'}`)
}

// 数据源表单管理
const addDataSource = () => {
  if (!nodeConfig.value.data_sources) {
    nodeConfig.value.data_sources = []
  }
  
  nodeConfig.value.data_sources.push({
    template_id: templates.value[0]?.id || 0,
    alias: `source${nodeConfig.value.data_sources.length + 1}`,
    filter_conditions: []
  })
}

const removeDataSource = (index: number) => {
  if (nodeConfig.value.data_sources) {
    nodeConfig.value.data_sources.splice(index, 1)
  }
}

const addFilterCondition = (sourceIndex: number) => {
  if (!nodeConfig.value.data_sources || !nodeConfig.value.data_sources[sourceIndex]) return
  
  if (!nodeConfig.value.data_sources[sourceIndex].filter_conditions) {
    nodeConfig.value.data_sources[sourceIndex].filter_conditions = []
  }
  
  nodeConfig.value.data_sources[sourceIndex].filter_conditions!.push({
    field: '',
    operator: 'eq',
    value: ''
  })
}

const removeFilterCondition = (sourceIndex: number, filterIndex: number) => {
  if (!nodeConfig.value.data_sources || !nodeConfig.value.data_sources[sourceIndex] || 
      !nodeConfig.value.data_sources[sourceIndex].filter_conditions) return
  
  nodeConfig.value.data_sources[sourceIndex].filter_conditions!.splice(filterIndex, 1)
}

const updateDataSourceFilters = (sourceIndex: number) => {
  // 当数据源模板变更时，清空筛选条件
  if (nodeConfig.value.data_sources && nodeConfig.value.data_sources[sourceIndex]) {
    nodeConfig.value.data_sources[sourceIndex].filter_conditions = []
  }
}

// 条件组管理（用于条件/并行分支节点）
const addConditionGroup = () => {
  if (!nodeConfig.value.condition_groups) {
    nodeConfig.value.condition_groups = []
  }
  nodeConfig.value.condition_groups.push({
    conditions: [{ type: 'field', field: '', operator: 'eq', value: '' }]
  })
}

const removeConditionGroup = (groupIndex: number) => {
  if (nodeConfig.value.condition_groups) {
    nodeConfig.value.condition_groups.splice(groupIndex, 1)
  }
}

const addCondition = (groupIndex: number) => {
  if (!nodeConfig.value.condition_groups || !nodeConfig.value.condition_groups[groupIndex]) return
  nodeConfig.value.condition_groups[groupIndex].conditions.push({
    type: 'field', field: '', operator: 'eq', value: ''
  })
}

const removeCondition = (groupIndex: number, condIndex: number) => {
  if (nodeConfig.value.condition_groups && nodeConfig.value.condition_groups[groupIndex]) {
    nodeConfig.value.condition_groups[groupIndex].conditions.splice(condIndex, 1)
  }
}

// 跨表数据操作：目标表单筛选条件管理
const addTargetFilterCondition = () => {
  if (!nodeConfig.value.filter_conditions) {
    nodeConfig.value.filter_conditions = []
  }
  nodeConfig.value.filter_conditions.push({
    field: '', operator: 'eq', value_type: 'field', value: ''
  })
}

const removeTargetFilterCondition = (index: number) => {
  if (nodeConfig.value.filter_conditions) {
    nodeConfig.value.filter_conditions.splice(index, 1)
  }
}

// 目标表单变更时重置字段映射
const handleTargetTemplateChange = (templateId?: number) => {
  if (!templateId) {
    nodeConfig.value.field_mappings = {}
    nodeConfig.value.filter_conditions = []
    return
  }
  // 初始化字段映射
  if (!nodeConfig.value.field_mappings) {
    nodeConfig.value.field_mappings = {}
  }
  const fields = getTemplateFields(templateId)
  fields.forEach(field => {
    if (!nodeConfig.value.field_mappings![field.name]) {
      nodeConfig.value.field_mappings![field.name] = { type: 'none', value: '' }
    }
  })
}

// 获取字段映射配置（如不存在则初始化）
const getFieldMapping = (fieldName: string) => {
  if (!nodeConfig.value.field_mappings) {
    nodeConfig.value.field_mappings = {}
  }
  if (!nodeConfig.value.field_mappings[fieldName]) {
    nodeConfig.value.field_mappings[fieldName] = { type: 'none', value: '' }
  }
  return nodeConfig.value.field_mappings[fieldName]
}

// 字段映射类型变更时清空值
const onFieldMappingTypeChange = (fieldName: string, newType: string) => {
  if (nodeConfig.value.field_mappings && nodeConfig.value.field_mappings[fieldName]) {
    nodeConfig.value.field_mappings[fieldName].value = ''
  }
}

// 数据填报节点：填报结束条件 - 数据源管理
const addFinishDataSource = () => {
  if (!nodeConfig.value.finish_data_sources) {
    nodeConfig.value.finish_data_sources = []
  }
  nodeConfig.value.finish_data_sources.push({ template_id: null, alias: '' })
}

const removeFinishDataSource = (index: number) => {
  if (nodeConfig.value.finish_data_sources) {
    nodeConfig.value.finish_data_sources.splice(index, 1)
  }
}

// 数据填报节点：填报结束条件 - 条件组管理
const addFinishConditionGroup = () => {
  if (!nodeConfig.value.finish_condition_groups) {
    nodeConfig.value.finish_condition_groups = []
  }
  nodeConfig.value.finish_condition_groups.push({
    conditions: [{ type: 'field', field: '', operator: 'eq', value: '' }]
  })
}

const removeFinishConditionGroup = (groupIndex: number) => {
  if (nodeConfig.value.finish_condition_groups) {
    nodeConfig.value.finish_condition_groups.splice(groupIndex, 1)
  }
}

const addFinishCondition = (groupIndex: number) => {
  if (!nodeConfig.value.finish_condition_groups || !nodeConfig.value.finish_condition_groups[groupIndex]) return
  nodeConfig.value.finish_condition_groups[groupIndex].conditions.push({
    type: 'field', field: '', operator: 'eq', value: ''
  })
}

const removeFinishCondition = (groupIndex: number, condIndex: number) => {
  if (nodeConfig.value.finish_condition_groups && nodeConfig.value.finish_condition_groups[groupIndex]) {
    nodeConfig.value.finish_condition_groups[groupIndex].conditions.splice(condIndex, 1)
  }
}

// 添加数据映射（旧接口保留兼容）
const addDataMapping = () => {
  if (!nodeConfig.value.data_mapping) {
    nodeConfig.value.data_mapping = {}
  }
  const key = `field_${Object.keys(nodeConfig.value.data_mapping).length + 1}`
  nodeConfig.value.data_mapping[key] = '{{value}}'
}

// 保存节点配置
const saveNodeConfig = () => {
  ElMessage.success('配置已保存')
}

// 获取节点图标
const getNodeIcon = (type: string) => {
  const icons: Record<string, string> = {
    start: 'VideoPlay',
    end: 'CircleCheck',
    approval: 'UserFilled',
    task: 'Document',
    cc: 'Message',
    data_fill: 'Edit',
    condition: 'Connection',
    parallel: 'Share',
    parallel_join: 'Sort',
    sub_process: 'SetUp',
    trigger: 'MagicStick',
    data_change: 'Refresh',
    add_data: 'Plus',
    update_data: 'Edit',
    delete_data: 'Delete',
    delay: 'Timer'
  }
  return icons[type] || 'CircleCheck'
}

// 返回列表
const goBack = () => {
  router.push('/workflows')
}

// 拖拽开始
const handleDragStart = (e: DragEvent, nodeType: any) => {
  e.dataTransfer?.setData('nodeType', JSON.stringify(nodeType))
}

// 放置节点
const handleDrop = (e: DragEvent) => {
  const data = e.dataTransfer?.getData('nodeType')
  if (!data) return
  
  const nodeType = JSON.parse(data)
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left - 75
  const y = e.clientY - rect.top - 30
  
  const newNode: WorkflowNode = {
    id: `${nodeType.type}-${Date.now()}`,
    type: nodeType.type,
    name: nodeType.name,
    description: '',
    x: Math.max(0, x),
    y: Math.max(0, y)
  }
  
  // 根据节点类型设置默认配置 - 斑斑低代码平台标准
  if (['approval', 'task', 'cc'].includes(nodeType.type)) {
    newNode.config = {
      approval_type: 'manual',
      approval_mode: 'regular',
      assignee_source: 'specified',
      assignee_ids: [],
      multi_person_mode: 'any',
      allow_transfer: false,
      require_comment: false,
      empty_assignee_action: 'admin_fallback',
      same_person_action: 'self_approve',
      allow_reject_back: false,
      reject_back_range: 'any',
      timeout_hours: 72,
      timeout_action: 'notify'
    }
  } else if (nodeType.type === 'condition') {
    newNode.config = {
      priority: 1,
      condition_groups: [
        { conditions: [{ type: 'field', field: '', operator: 'eq', value: '' }] }
      ]
    }
  } else if (nodeType.type === 'parallel') {
    newNode.config = {
      condition_groups: []
    }
  } else if (nodeType.type === 'trigger') {
    newNode.config = {
      trigger_type: 'data_change',
      change_types: ['create', 'update', 'delete']
    }
  } else if (nodeType.type === 'data_change') {
    newNode.config = {
      operation_type: 'update',
      data_mapping: {},
      filter_conditions: []
    }
  } else if (['add_data', 'update_data', 'delete_data'].includes(nodeType.type)) {
    newNode.config = {
      target_template_id: undefined,
      field_mappings: {},
      filter_conditions: [],
      filter_logic: 'and',
      data_sources: []
    }
  } else if (nodeType.type === 'delay') {
    newNode.config = {
      delay_seconds: 3600
    }
  } else if (nodeType.type === 'sub_process') {
    newNode.config = {
      sub_workflow_id: 0
    }
  } else if (nodeType.type === 'data_fill') {
    newNode.config = {
      assignee_source: 'submitter',
      assignee_ids: [],
      assignee_field: '',
      manager_order: 'bottom_up',
      manager_level: 'direct',
      empty_assignee_action: 'admin_fallback',
      fallback_assignee_id: null,
      allow_transfer: false,
      require_comment: false,
      timeout_hours: 0,
      timeout_action: 'notify',
      field_permissions: {},
      enable_finish_condition: false,
      finish_data_sources: [],
      finish_condition_groups: []
    }
  }
  
  nodes.value.push(newNode)
  ElMessage.success('添加节点成功')
}

// 开始拖拽节点
const startDrag = (e: MouseEvent, node: WorkflowNode) => {
  isDragging.value = true
  dragNode.value = node
  dragOffset.value = {
    x: e.clientX - node.x,
    y: e.clientY - node.y
  }
}

// 选择节点
const selectNode = (nodeId: string) => {
  selectedNode.value = nodeId
  selectedConnection.value = null
}

// 取消选择
const deselectNode = () => {
  selectedNode.value = null
  selectedConnection.value = null
}

// 选择连接线
const selectConnection = (connId: string) => {
  selectedConnection.value = connId
  selectedNode.value = null
}

// 开始连线
const startConnection = (e: MouseEvent, nodeId: string, type: string) => {
  e.stopPropagation()
  isConnecting.value = true
  connectionStart.value = { nodeId, type }
  mousePosition.value = { x: e.clientX, y: e.clientY }
  updatePreviewPath()
}

// 更新预览路径
const updatePreviewPath = () => {
  if (!isConnecting.value || !connectionStart.value) return
  
  const startNode = nodes.value.find(n => n.id === connectionStart.value!.nodeId)
  if (!startNode) return
  
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const startX = startNode.x + 150
  const startY = startNode.y + 30
  const endX = mousePosition.value.x - rect.left
  const endY = mousePosition.value.y - rect.top
  
  const midX = (startX + endX) / 2
  
  previewPath.value = `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`
}

// 创建连接
const createConnection = (e: MouseEvent) => {
  if (!connectionStart.value) return
  
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top
  
  // 找到鼠标点击的节点
  const targetNode = nodes.value.find(node => {
    return mouseX >= node.x && mouseX <= node.x + 150 && 
           mouseY >= node.y && mouseY <= node.y + 80
  })
  
  if (targetNode && targetNode.id !== connectionStart.value.nodeId) {
    // 检查是否已存在相同连接
    const existingConnection = connections.value.find(
      conn => conn.from === connectionStart.value!.nodeId && conn.to === targetNode.id
    )
    
    if (!existingConnection) {
      const newConnection: Connection = {
        id: `conn-${Date.now()}`,
        from: connectionStart.value.nodeId,
        to: targetNode.id,
        path: generatePath(
          nodes.value.find(n => n.id === connectionStart.value!.nodeId)!,
          targetNode
        )
      }
      connections.value.push(newConnection)
      ElMessage.success('连接成功')
    } else {
      ElMessage.warning('该连接已存在')
    }
  }
}

// 删除节点
const deleteNode = () => {
  if (!selectedNode.value) return
  
  ElMessageBox.confirm('确定删除该节点吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    nodes.value = nodes.value.filter(n => n.id !== selectedNode.value)
    connections.value = connections.value.filter(
      c => c.from !== selectedNode.value && c.to !== selectedNode.value
    )
    selectedNode.value = null
    ElMessage.success('删除成功')
  })
}

// 保存流程
const saveWorkflow = async () => {
  try {
    // 验证流程
    const errors: string[] = []
    
    // 检查开始节点
    const startNodes = nodes.value.filter(n => n.type === 'start')
    if (startNodes.length === 0) {
      errors.push('缺少开始节点')
    } else if (startNodes.length > 1) {
      errors.push('只能有一个开始节点')
    }
    
    // 检查结束节点
    const endNodes = nodes.value.filter(n => n.type === 'end')
    if (endNodes.length === 0) {
      errors.push('缺少结束节点')
    }
    
    if (errors.length > 0) {
      ElMessageBox.alert(errors.join('<br>'), '验证失败', {
        dangerouslyUseHTMLString: true,
        type: 'error'
      })
      return
    }
    
    // 构建API请求数据
    const workflowData = {
      name: workflowName.value,
      description: `流程设计 ${new Date().toLocaleDateString()}`,
      flow_type: 'normal',
      nodes: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        config: node.config || {}
      })),
      edges: connections.value.map(conn => ({
        id: conn.id,
        source: conn.from,
        target: conn.to,
        label: conn.label || '',
        condition: {} // 可以从conn.label解析条件
      })),
      // 斑斑低代码平台扩展字段
      node_definitions: nodes.value.map(node => ({
        id: node.id,
        type: node.type,
        name: node.name,
        config: node.config || {}
      })),
      edge_definitions: connections.value.map(conn => ({
        id: conn.id,
        source: conn.from,
        target: conn.to,
        label: conn.label || '',
        condition: {} // 条件定义
      })),
      variables: {},
      form_template_id: findPrimaryFormTemplateId()
    }
    
    // 调用API保存
    if (workflowId && workflowId !== 'new') {
      await workflowAPI.update(parseInt(workflowId), workflowData)
      ElMessage.success('流程更新成功')
    } else {
      const response = await workflowAPI.create(workflowData)
      // 更新路由ID
      router.push(`/workflows/design/${response.id}`)
      ElMessage.success('流程创建成功')
    }
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
  }
}

// 查找主表单模板ID
const findPrimaryFormTemplateId = () => {
  // 首先查找开始节点后的第一个审批/办理节点
  const approvalNode = nodes.value.find(node => 
    ['approval', 'task', 'data_fill'].includes(node.type) && 
    node.config?.form_template_id
  )
  if (approvalNode?.config?.form_template_id) {
    return approvalNode.config.form_template_id
  }
  
  // 否则查找第一个有表单模板的节点
  const formNode = nodes.value.find(node => node.config?.form_template_id)
  return formNode?.config?.form_template_id || null
}

// 验证流程
const validateWorkflow = () => {
  const errors: string[] = []
  
  // 检查开始节点
  const startNodes = nodes.value.filter(n => n.type === 'start')
  if (startNodes.length === 0) {
    errors.push('缺少开始节点')
  } else if (startNodes.length > 1) {
    errors.push('只能有一个开始节点')
  }
  
  // 检查结束节点
  const endNodes = nodes.value.filter(n => n.type === 'end')
  if (endNodes.length === 0) {
    errors.push('缺少结束节点')
  }
  
  // 检查孤立节点
  const connectedNodes = new Set<string>()
  connections.value.forEach(conn => {
    connectedNodes.add(conn.from)
    connectedNodes.add(conn.to)
  })
  
  nodes.value.forEach(node => {
    if (!connectedNodes.has(node.id) && node.type !== 'start') {
      errors.push(`节点 "${node.name}" 未连接`)
    }
  })
  
  if (errors.length > 0) {
    ElMessageBox.alert(errors.join('<br>'), '验证失败', {
      dangerouslyUseHTMLString: true,
      type: 'error'
    })
  } else {
    ElMessage.success('流程验证通过')
  }
}

// 预览流程
const previewWorkflow = () => {
  ElMessageBox.alert('流程预览功能开发中...', '提示')
}

// 更新连接线
const updateConnections = () => {
  connections.value.forEach(conn => {
    const fromNode = nodes.value.find(n => n.id === conn.from)
    const toNode = nodes.value.find(n => n.id === conn.to)
    if (fromNode && toNode) {
      conn.path = generatePath(fromNode, toNode)
    }
  })
}

// 生成路径
const generatePath = (from: WorkflowNode, to: WorkflowNode) => {
  const startX = from.x + 150
  const startY = from.y + 30
  const endX = to.x
  const endY = to.y + 30
  
  const midX = (startX + endX) / 2
  
  return `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`
}

// 全局鼠标事件
const handleMouseMove = (e: MouseEvent) => {
  if (isDragging.value && dragNode.value) {
    dragNode.value.x = e.clientX - dragOffset.value.x
    dragNode.value.y = e.clientY - dragOffset.value.y
    updateConnections()
  } else if (isConnecting.value && connectionStart.value) {
    // 更新鼠标位置
    mousePosition.value = { x: e.clientX, y: e.clientY }
    // 更新预览路径
    updatePreviewPath()
  }
}

const handleMouseUp = (e: MouseEvent) => {
  if (isDragging.value) {
    isDragging.value = false
    dragNode.value = null
  } else if (isConnecting.value && connectionStart.value) {
    // 尝试创建连接
    createConnection(e)
  }
  isConnecting.value = false
  connectionStart.value = null
  previewPath.value = ''
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  initData()
})

onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
})
</script>

<style scoped lang="scss">
.workflow-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.designer-header {
  padding: 16px;
  border-bottom: 1px solid #e6e6e6;
  background: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.toolbox {
  width: 200px;
  background: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  padding: 16px;
  
  h4 {
    margin-bottom: 16px;
  }
}

.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  }
}

.canvas {
  flex: 1;
  position: relative;
  background: #fafafa;
  background-image: 
    linear-gradient(#e6e6e6 1px, transparent 1px),
    linear-gradient(90deg, #e6e6e6 1px, transparent 1px);
  background-size: 20px 20px;
  overflow: hidden;
}

.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: all;
}

.connection-line {
  fill: none;
  stroke: #909399;
  stroke-width: 2;
  pointer-events: stroke;
  cursor: pointer;
  
  &:hover, &.selected {
    stroke: #409eff;
    stroke-width: 3;
  }
  
  &.preview {
    stroke: #409eff;
    stroke-width: 2;
    stroke-dasharray: 5,5;
  }
}

.workflow-node {
  position: absolute;
  width: 150px;
  background: white;
  border: 2px solid #dcdfe6;
  border-radius: 4px;
  cursor: move;
  user-select: none;
  
  &.selected {
    border-color: #409eff;
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
  }
  
  .node-header {
    padding: 8px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: bold;
    border-bottom: 1px solid #e6e6e6;
    
    &.start { background: #67c23a; color: white; }
    &.task { background: #409eff; color: white; }
    &.condition { background: #e6a23c; color: white; }
    &.parallel { background: #909399; color: white; }
    &.end { background: #f56c6c; color: white; }
  }
  
  .node-body {
    padding: 8px 12px;
    font-size: 12px;
    color: #606266;
    min-height: 40px;
  }
  
  .node-ports {
    position: relative;
    height: 20px;
    
    .port {
      position: absolute;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #909399;
      cursor: crosshair;
      
      &:hover {
        background: #409eff;
        transform: scale(1.2);
      }
      
      &.input {
        left: -6px;
        top: 4px;
      }
      
      &.output {
        right: -6px;
        top: 4px;
      }
    }
  }
}

.properties {
  width: 300px;
  background: #f5f7fa;
  border-left: 1px solid #e6e6e6;
  padding: 16px;
  overflow-y: auto;
  
  h4 {
    margin-bottom: 16px;
  }
}

.empty-properties {
  padding: 40px 0;
}

.property-form {
  :deep(.el-tabs) {
    .el-tabs__nav-wrap::after {
      display: none;
    }
  }
  
  .form-tip {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }
  
  .mapping-item {
    margin-bottom: 8px;
  }
  
  .property-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
  }
}

// 权限配置样式
.permission-container {
  padding: 10px;
  
  .permission-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e6e6e6;
    
    span {
      font-weight: bold;
      font-size: 14px;
    }
    
    .el-button {
      margin-left: 8px;
    }
  }
  
  .permission-tip {
    margin-top: 20px;
    padding: 12px;
    background: #f0f9ff;
    border-radius: 4px;
    border-left: 4px solid #409eff;
    
    p {
      margin: 4px 0;
      font-size: 12px;
      color: #606266;
      
      strong {
        color: #303133;
      }
    }
  }
}

// 数据源配置样式
.data-source-list {
  .empty-data-sources {
    padding: 16px;
    text-align: center;
    color: #909399;
    background: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 12px;
  }
  
  .data-source-items {
    margin-bottom: 16px;
  }
  
  .data-source-item {
    padding: 12px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    margin-bottom: 12px;
    background: white;
    
    .source-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid #f0f0f0;
      
      span {
        font-weight: bold;
        font-size: 13px;
      }
    }
    
    .source-content {
      .filter-conditions {
        margin-top: 12px;
        
        .filter-item {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          padding: 8px;
          background: #f9f9f9;
          border-radius: 4px;
        }
      }
    }
  }
}

// 节点配置表单样式
.node-config-form {
  .divider-title {
    font-size: 12px;
    font-weight: bold;
    color: #606266;
  }
  
  .unit-label {
    margin-left: 8px;
    font-size: 12px;
    color: #909399;
  }
}

// 条件组样式
.condition-groups {
  .condition-group {
    border: 1px solid #e6e6e6;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 10px;
    background: #fafafa;
    position: relative;
    
    .group-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      
      .or-label {
        font-size: 11px;
        font-weight: bold;
        color: #E6A23C;
        background: #fdf6ec;
        padding: 2px 6px;
        border-radius: 10px;
      }
    }
    
    .cond-row {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 4px;
      padding: 6px;
      background: white;
      border-radius: 4px;
      border: 1px solid #f0f0f0;
    }
  }
}

// 字段映射表格样式
.field-mapping-table {
  border: 1px solid #e6e6e6;
  border-radius: 4px;
  overflow: hidden;
  
  .mapping-header {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    background: #f5f7fa;
    border-bottom: 1px solid #e6e6e6;
    font-size: 12px;
    font-weight: bold;
    color: #606266;
  }
  
  .mapping-row {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 12px;
    
    &:last-child { border-bottom: none; }
    &:hover { background: #f9fafc; }
    
    .field-name {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #303133;
    }
  }
}

// 目标筛选条件行
.condition-list {
  .condition-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px;
    background: #f9f9f9;
    border-radius: 4px;
    border: 1px solid #f0f0f0;
  }
}
</style>
