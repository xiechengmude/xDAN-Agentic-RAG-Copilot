#!/bin/bash

echo "🚀 启动 Langfuse v2..."
echo "=========================="

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose -f docker-compose.langfuse-v2.yml down

# 启动服务
echo "▶️  启动服务..."
docker-compose -f docker-compose.langfuse-v2.yml up -d

echo "⏳ 等待服务启动..."
sleep 20

# 检查服务状态
echo "🔍 检查服务状态..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Langfuse 启动成功！"
else
    echo "⚠️  服务可能还在启动中，请稍等..."
    sleep 10
fi

# 执行修复（如果需要）
echo "🔧 检查并修复项目成员关系..."
docker exec langfuse-db psql -U langfuse -d langfuse -c "
DO \$\$
DECLARE
    user_record RECORD;
    org_membership_record RECORD;
    project_record RECORD;
BEGIN
    FOR user_record IN 
        SELECT id, email FROM users WHERE email = 'admin@example.com'
    LOOP
        SELECT INTO org_membership_record id, org_id 
        FROM organization_memberships 
        WHERE user_id = user_record.id;
        
        IF FOUND THEN
            SELECT INTO project_record id 
            FROM projects 
            WHERE id = 'default-project';
            
            IF FOUND THEN
                IF NOT EXISTS (
                    SELECT 1 FROM project_memberships 
                    WHERE user_id = user_record.id 
                    AND project_id = project_record.id
                ) THEN
                    INSERT INTO project_memberships (
                        user_id, 
                        project_id, 
                        role, 
                        org_membership_id,
                        created_at,
                        updated_at
                    ) VALUES (
                        user_record.id,
                        project_record.id,
                        'OWNER',
                        org_membership_record.id,
                        NOW(),
                        NOW()
                    );
                    RAISE NOTICE '✅ 已添加用户到项目';
                ELSE
                    RAISE NOTICE '✅ 用户已经是项目成员';
                END IF;
            END IF;
        END IF;
    END LOOP;
END \$\$;" 2>/dev/null || echo "⏳ 等待数据初始化完成..."

echo ""
echo "🎉 Langfuse v2 启动完成！"
echo "=========================="
echo "🌐 访问地址: http://localhost:3000"
echo "👤 用户名: admin@example.com"
echo "🔑 密码: admin123456"
echo ""
echo "💡 如果首次启动遇到 Traces 页面错误，请等待 1-2 分钟后刷新页面" 