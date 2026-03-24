import type { App } from "vue";
import { ElButton } from "element-plus/es/components/button/index";
import { ElCard } from "element-plus/es/components/card/index";
import { ElCheckbox, ElCheckboxGroup } from "element-plus/es/components/checkbox/index";
import { ElContainer, ElHeader, ElMain } from "element-plus/es/components/container/index";
import { ElDatePicker } from "element-plus/es/components/date-picker/index";
import { ElDialog } from "element-plus/es/components/dialog/index";
import { ElDrawer } from "element-plus/es/components/drawer/index";
import { ElEmpty } from "element-plus/es/components/empty/index";
import { ElForm, ElFormItem } from "element-plus/es/components/form/index";
import { ElIcon } from "element-plus/es/components/icon/index";
import { ElInput } from "element-plus/es/components/input/index";
import { ElLoadingDirective } from "element-plus/es/components/loading/index";
import { ElOption, ElSelect } from "element-plus/es/components/select/index";
import { ElRadio, ElRadioButton, ElRadioGroup } from "element-plus/es/components/radio/index";
import { ElSkeleton } from "element-plus/es/components/skeleton/index";
import { ElSlider } from "element-plus/es/components/slider/index";
import { ElSpace } from "element-plus/es/components/space/index";
import { ElSwitch } from "element-plus/es/components/switch/index";
import { ElTabPane, ElTabs } from "element-plus/es/components/tabs/index";
import { ElTag } from "element-plus/es/components/tag/index";
import { ElTimeline, ElTimelineItem } from "element-plus/es/components/timeline/index";
import { ElUpload } from "element-plus/es/components/upload/index";

import "element-plus/es/components/base/style/css";
import "element-plus/es/components/button/style/css";
import "element-plus/es/components/card/style/css";
import "element-plus/es/components/checkbox/style/css";
import "element-plus/es/components/checkbox-group/style/css";
import "element-plus/es/components/container/style/css";
import "element-plus/es/components/date-picker/style/css";
import "element-plus/es/components/dialog/style/css";
import "element-plus/es/components/drawer/style/css";
import "element-plus/es/components/empty/style/css";
import "element-plus/es/components/form/style/css";
import "element-plus/es/components/form-item/style/css";
import "element-plus/es/components/icon/style/css";
import "element-plus/es/components/input/style/css";
import "element-plus/es/components/loading/style/css";
import "element-plus/es/components/select/style/css";
import "element-plus/es/components/option/style/css";
import "element-plus/es/components/radio/style/css";
import "element-plus/es/components/radio-button/style/css";
import "element-plus/es/components/radio-group/style/css";
import "element-plus/es/components/skeleton/style/css";
import "element-plus/es/components/slider/style/css";
import "element-plus/es/components/space/style/css";
import "element-plus/es/components/switch/style/css";
import "element-plus/es/components/tabs/style/css";
import "element-plus/es/components/tab-pane/style/css";
import "element-plus/es/components/tag/style/css";
import "element-plus/es/components/timeline/style/css";
import "element-plus/es/components/timeline-item/style/css";
import "element-plus/es/components/upload/style/css";

const components = [
  ElButton,
  ElCard,
  ElCheckbox,
  ElCheckboxGroup,
  ElContainer,
  ElDatePicker,
  ElDialog,
  ElDrawer,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElMain,
  ElOption,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElSelect,
  ElSkeleton,
  ElSlider,
  ElSpace,
  ElSwitch,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElUpload,
];

export function installElement(app: App) {
  components.forEach((component) => {
    app.use(component);
  });
  app.directive("loading", ElLoadingDirective);
}
