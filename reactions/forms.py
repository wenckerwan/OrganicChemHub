"""Frontend forms (v4.0)."""

from django import forms

from .models import Comment


class CommentForm(forms.Form):
    body = forms.CharField(
        label="评论内容",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "写下你的评论…", "class": "form-control"}),
    )
    parent_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if not body:
            raise forms.ValidationError("评论内容不能为空。")
        return body

    def clean_parent_id(self):
        value = self.cleaned_data.get("parent_id")
        if value and value < 0:
            raise forms.ValidationError("无效的回复目标。")
        return value
