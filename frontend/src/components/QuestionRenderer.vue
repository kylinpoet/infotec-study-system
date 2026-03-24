<template>
  <div class="question-card">
    <div class="question-head">
      <el-tag effect="light" round>第 {{ index + 1 }} 题</el-tag>
      <el-tag type="info" effect="plain" round>{{ question.type }}</el-tag>
      <el-tag type="warning" effect="plain" round>{{ question.points }} 分</el-tag>
    </div>
    <h4>{{ question.stem }}</h4>

    <el-radio-group
      v-if="question.type === 'single_choice'"
      :model-value="modelValue as string | undefined"
      class="question-radio-group"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <el-radio-button v-for="option in question.options" :key="option" :label="option">
        {{ option }}
      </el-radio-button>
    </el-radio-group>

    <template v-else>
      <p class="panel-note">
        {{ question.type === "sequence" ? "请用 > 连接各步骤。" : "请输入关键词或简要答案。" }}
      </p>
      <el-input
        :model-value="String(modelValue ?? '')"
        type="textarea"
        :rows="3"
        resize="vertical"
        @input="$emit('update:modelValue', $event)"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import type { QuestionSpec } from "../types/contracts";

defineProps<{
  index: number;
  question: QuestionSpec;
  modelValue: unknown;
}>();

defineEmits<{
  "update:modelValue": [value: unknown];
}>();
</script>
