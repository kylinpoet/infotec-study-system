export interface ZodiacAgentVisual {
  key: string;
  label: string;
  animal: string;
  description: string;
  primary: string;
  secondary: string;
  accent: string;
}

export const zodiacAgents: ZodiacAgentVisual[] = [
  { key: "rat", label: "机灵鼠", animal: "鼠", description: "提问快、反应快", primary: "#7C8CF8", secondary: "#DEE5FF", accent: "#4755D7" },
  { key: "ox", label: "稳健牛", animal: "牛", description: "稳步拆解任务", primary: "#3B82F6", secondary: "#DBECFF", accent: "#0F4CB8" },
  { key: "tiger", label: "探索虎", animal: "虎", description: "适合挑战任务", primary: "#F97316", secondary: "#FFE7D2", accent: "#C24A00" },
  { key: "rabbit", label: "灵感兔", animal: "兔", description: "温和鼓励型", primary: "#EC4899", secondary: "#FFE0F0", accent: "#B61C73" },
  { key: "dragon", label: "领航龙", animal: "龙", description: "适合课堂引导", primary: "#14B8A6", secondary: "#D8FBF5", accent: "#0B7B70" },
  { key: "snake", label: "推理蛇", animal: "蛇", description: "逻辑分析型", primary: "#8B5CF6", secondary: "#E9DEFF", accent: "#6131C5" },
  { key: "horse", label: "行动马", animal: "马", description: "节奏推进型", primary: "#F59E0B", secondary: "#FFF0C9", accent: "#B97700" },
  { key: "goat", label: "共创羊", animal: "羊", description: "适合协作反馈", primary: "#22C55E", secondary: "#DDF9E7", accent: "#13863D" },
  { key: "monkey", label: "创客猴", animal: "猴", description: "创客灵感型", primary: "#F97373", secondary: "#FFE0E0", accent: "#D53F3F" },
  { key: "rooster", label: "晨光鸡", animal: "鸡", description: "清单复盘型", primary: "#EF4444", secondary: "#FFE2D7", accent: "#B42318" },
  { key: "dog", label: "守护狗", animal: "狗", description: "陪伴鼓励型", primary: "#0EA5E9", secondary: "#DDF5FF", accent: "#0A6E99" },
  { key: "pig", label: "圆梦猪", animal: "猪", description: "成长鼓劲型", primary: "#FB7185", secondary: "#FFE2E8", accent: "#C7375A" },
];

export const zodiacAgentMap = Object.fromEntries(zodiacAgents.map((item) => [item.key, item])) as Record<string, ZodiacAgentVisual>;

