from django import forms
from .models import ClusterRun
from .services import MIN_K, MAX_K

class UploadForm(forms.Form):
    file = forms.FileField(label="County indicators CSV")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        return f

class RunForm(forms.Form):
    algorithm = forms.ChoiceField(choices=ClusterRun.ALGORITHMS)
    k = forms.IntegerField(min_value=MIN_K, max_value=MAX_K, required=False,
                           help_text="Leave blank to use the k with the best silhouette score.")
