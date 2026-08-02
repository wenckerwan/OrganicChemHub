from django import forms

from .models import Message


class ReactionCsvImportForm(forms.Form):
    target = forms.ChoiceField(label="导入目标", choices=(("named", "人名反应"), ("general", "常见有机反应")))
    mode = forms.ChoiceField(label="导入模式", choices=(("create", "仅新增"), ("upsert", "新增并更新")))
    csv_file = forms.FileField(label="CSV 文件")


class MessageBroadcastForm(forms.Form):
    target = forms.ChoiceField(label="接收范围", choices=(("all", "全部用户"), ("selected", "选中用户")))
    msg_type = forms.ChoiceField(label="消息类型", choices=Message.Type.choices)
    title = forms.CharField(label="标题", max_length=200)
    content = forms.CharField(label="内容", widget=forms.Textarea)


class MessageCleanupForm(forms.Form):
    older_than = forms.ChoiceField(label="清理范围", choices=(("3", "3 个月前"), ("6", "6 个月前"), ("12", "1 年前")))
    read_only = forms.BooleanField(label="只清理已读消息", initial=True, required=False)
    confirm = forms.BooleanField(label="确认删除", required=False)


class ResourceImportOrUploadForm(forms.Form):
    title = forms.CharField(label="标题", max_length=255, required=False)
    category = forms.CharField(label="分类", max_length=30, required=False)
    uploaded_file = forms.FileField(label="上传文件", required=False)
    external_path = forms.CharField(label="外部路径", widget=forms.Textarea, required=False)