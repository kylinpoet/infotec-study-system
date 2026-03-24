from app.schemas.contracts import ActivityDraftRequest, ActivitySpec, QuestionSpec


COMPONENT_STEMS = {
    "single_choice": "以下哪种课堂场景更适合让 AI 先完成首轮处理？",
    "sequence": "请按正确顺序整理本课任务流程，使用 `>` 连接。",
    "hotspot": "请指出示例截图中最需要人工复核的关键位置或关键词。",
    "flow_link": "请把活动步骤按正确逻辑连接起来。",
}


def build_activity_spec(payload: ActivityDraftRequest) -> ActivitySpec:
    whitelist = payload.component_whitelist or ["single_choice", "sequence", "hotspot"]
    selected_components = whitelist[:3]

    questions: list[QuestionSpec] = []
    for index, component in enumerate(selected_components, start=1):
        if component == "single_choice":
            questions.append(
                QuestionSpec(
                    key=f"q{index}",
                    type="single_choice",
                    stem=COMPONENT_STEMS[component],
                    options=[
                        "直接发布未经教师审核的高风险内容",
                        "说明文、流程任务或规范判断题",
                        "完全绕过人工复核",
                        "只用截图判断全部学习结果",
                    ],
                    correct_answer="说明文、流程任务或规范判断题",
                    points=30,
                )
            )
        elif component == "sequence":
            questions.append(
                QuestionSpec(
                    key=f"q{index}",
                    type="sequence",
                    stem=f"{payload.learning_goal}。{COMPONENT_STEMS[component]}",
                    options=["输入教学目标", "AI 生成草案", "教师预览修改", "学生作答回流"],
                    correct_answer=["输入教学目标", "AI 生成草案", "教师预览修改", "学生作答回流"],
                    points=40,
                )
            )
        else:
            questions.append(
                QuestionSpec(
                    key=f"q{index}",
                    type=component,
                    stem=COMPONENT_STEMS.get(component, "请完成本题。"),
                    options=["术语区域", "标题区域", "配图区域", "页脚区域"],
                    correct_answer="术语区域",
                    points=30,
                )
            )

    return ActivitySpec(
        title=payload.title or "AI 交互作业草案",
        instructions=(
            f"围绕“{payload.learning_goal}”生成的结构化作业草案。"
            "教师可以在发布前继续调整题目、说明和时间设置。"
        ),
        teacher_tip="建议先查看高错误率题目，再调用课程智能体生成补充练习与讲评提纲。",
        component_whitelist=whitelist,
        questions=questions,
    )
