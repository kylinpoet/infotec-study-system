<template>
  <div
    class="assistant-float"
    :class="{ 'assistant-float--expanded': isExpanded, 'assistant-float--dragging': dragging }"
    :style="floatStyle"
    @mouseenter="hovered = true"
    @mouseleave="hovered = false"
  >
    <button
      type="button"
      class="assistant-float__trigger"
      @pointerdown="startDrag"
      @click="handleTriggerClick"
    >
      <div class="assistant-float__avatar">
        <ZodiacAgentAvatar :animal-key="session.user?.avatar ?? 'dragon'" compact />
      </div>
      <span class="assistant-float__badge">{{ badgeLabel }}</span>
    </button>

    <section class="assistant-float__panel">
      <header class="assistant-float__head">
        <div>
          <p class="panel-kicker">{{ badgeLabel }}助手</p>
          <h4>{{ assistant.title }}</h4>
          <p class="panel-note">{{ assistant.subtitle }}</p>
        </div>
        <button
          v-if="pinned"
          type="button"
          class="assistant-float__pin"
          @click.stop="pinned = false"
        >
          收起
        </button>
      </header>

      <div class="assistant-float__body">
        <section class="assistant-float__section">
          <div class="assistant-float__section-head">
            <strong>快捷提示</strong>
            <span>{{ visibleSuggestions.length }} 条</span>
          </div>
          <div class="assistant-float__suggestions">
            <button
              v-for="suggestion in visibleSuggestions"
              :key="suggestion"
              type="button"
              class="assistant-float__suggestion"
              @click="$emit('suggest', suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
        </section>

        <section v-if="assistant.agents.length" class="assistant-float__section">
          <div class="assistant-float__section-head">
            <strong>协作智能体</strong>
            <span>{{ assistant.agents.length }} 个</span>
          </div>
          <div class="assistant-float__agent-list">
            <article
              v-for="agent in assistant.agents.slice(0, 3)"
              :key="agent.id"
              class="assistant-float__agent"
            >
              <div>
                <strong>{{ agent.name }}</strong>
                <p class="panel-note">{{ agent.role }} · {{ agent.scope_label }}</p>
              </div>
              <el-tag round size="small" type="success">{{ agent.status }}</el-tag>
            </article>
          </div>
        </section>

        <section v-if="assistant.external_sources_note" class="assistant-float__section">
          <div class="assistant-float__section-head">
            <strong>知识边界</strong>
            <el-tag
              round
              size="small"
              :type="assistant.allow_external_sources ? 'warning' : 'info'"
            >
              {{ assistant.allow_external_sources ? "可接外部站点" : "平台内知识" }}
            </el-tag>
          </div>
          <p class="panel-note">{{ assistant.external_sources_note }}</p>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import ZodiacAgentAvatar from "./ZodiacAgentAvatar.vue";

import { useSessionStore } from "../stores/session";
import type { AssistantDescriptor } from "../types/contracts";

const props = withDefaults(
  defineProps<{
    modelValue?: boolean;
    assistant: AssistantDescriptor;
  }>(),
  {
    modelValue: false,
  }
);

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  suggest: [value: string];
}>();

const session = useSessionStore();
const hovered = ref(false);
const pinned = ref(props.modelValue);
const dragging = ref(false);
const topOffset = ref(260);
const suppressToggle = ref(false);

let dragStartY = 0;
let dragStartTop = 0;
let dragMoved = false;

watch(
  () => props.modelValue,
  (value) => {
    pinned.value = value;
  }
);

watch(pinned, (value) => {
  emit("update:modelValue", value);
});

const isExpanded = computed(() => hovered.value || pinned.value);
const visibleSuggestions = computed(() => props.assistant.suggestions.slice(0, 4));
const floatStyle = computed(() => ({
  top: `${topOffset.value}px`
}));
const badgeLabel = computed(() => {
  const title = props.assistant.title;
  return title.includes("课程") ? "课程" : "通用";
});

onMounted(() => {
  if (typeof window === "undefined") {
    return;
  }
  const stored = window.localStorage.getItem("assistant-float-top");
  if (stored) {
    topOffset.value = clampTop(Number(stored));
  } else {
    topOffset.value = clampTop(window.innerHeight * 0.42);
  }
  window.addEventListener("resize", handleResize);
});

onBeforeUnmount(() => {
  if (typeof window === "undefined") {
    return;
  }
  window.removeEventListener("resize", handleResize);
  detachDragListeners();
});

function clampTop(value: number) {
  if (typeof window === "undefined") {
    return value;
  }
  const maxTop = Math.max(window.innerHeight - 140, 120);
  return Math.min(Math.max(value, 96), maxTop);
}

function handleResize() {
  topOffset.value = clampTop(topOffset.value);
}

function handleTriggerClick() {
  if (suppressToggle.value) {
    suppressToggle.value = false;
    return;
  }
  pinned.value = !pinned.value;
}

function startDrag(event: PointerEvent) {
  if (event.button !== 0) {
    return;
  }
  dragging.value = true;
  hovered.value = true;
  dragStartY = event.clientY;
  dragStartTop = topOffset.value;
  dragMoved = false;
  attachDragListeners();
}

function attachDragListeners() {
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", stopDrag);
  window.addEventListener("pointercancel", stopDrag);
}

function detachDragListeners() {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", stopDrag);
  window.removeEventListener("pointercancel", stopDrag);
}

function onPointerMove(event: PointerEvent) {
  if (!dragging.value) {
    return;
  }
  const deltaY = event.clientY - dragStartY;
  if (Math.abs(deltaY) > 4) {
    dragMoved = true;
  }
  topOffset.value = clampTop(dragStartTop + deltaY);
}

function stopDrag() {
  if (!dragging.value) {
    return;
  }
  dragging.value = false;
  detachDragListeners();
  if (dragMoved) {
    suppressToggle.value = true;
    window.setTimeout(() => {
      suppressToggle.value = false;
    }, 120);
  }
  window.localStorage.setItem("assistant-float-top", String(topOffset.value));
}
</script>
