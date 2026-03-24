<template>
  <el-drawer
    :model-value="modelValue"
    :title="assistant.title"
    size="420px"
    class="assistant-drawer"
    @close="$emit('update:modelValue', false)"
  >
    <div class="assistant-drawer__body">
      <section class="assistant-block">
        <div class="assistant-hero">
          <ZodiacAgentAvatar :animal-key="session.user?.avatar ?? 'dragon'" compact />
          <div class="assistant-hero__meta">
            <h4>{{ assistant.title }}</h4>
            <p class="panel-note">{{ assistant.subtitle }}</p>
          </div>
        </div>
        <div class="assistant-suggestion-list">
          <el-button
            v-for="suggestion in assistant.suggestions"
            :key="suggestion"
            class="assistant-suggestion"
            round
            text
            @click="$emit('suggest', suggestion)"
          >
            {{ suggestion }}
          </el-button>
        </div>
      </section>

      <section v-if="assistant.agents.length" class="assistant-block">
        <div class="drawer-subhead">
          <h4>已绑定智能体</h4>
        </div>
        <el-space direction="vertical" fill :size="12">
          <el-card v-for="agent in assistant.agents" :key="agent.id" shadow="never" class="assistant-agent-card">
            <div class="assistant-agent-card__row">
              <div>
                <strong>{{ agent.name }}</strong>
                <p class="panel-note">{{ agent.role }} · {{ agent.scope_label }}</p>
              </div>
              <el-tag type="success" effect="light">{{ agent.status }}</el-tag>
            </div>
          </el-card>
        </el-space>
      </section>

      <section v-if="assistant.external_sources_note" class="assistant-block">
        <div class="drawer-subhead">
          <h4>外部来源</h4>
          <el-tag :type="assistant.allow_external_sources ? 'warning' : 'info'" effect="light" round>
            {{ assistant.allow_external_sources ? "允许白名单接入" : "仅平台内知识" }}
          </el-tag>
        </div>
        <p class="panel-note">{{ assistant.external_sources_note }}</p>
      </section>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import ZodiacAgentAvatar from "./ZodiacAgentAvatar.vue";

import { useSessionStore } from "../stores/session";
import type { AssistantDescriptor } from "../types/contracts";

const session = useSessionStore();

defineProps<{
  modelValue: boolean;
  assistant: AssistantDescriptor;
}>();

defineEmits<{
  "update:modelValue": [value: boolean];
  suggest: [value: string];
}>();
</script>
