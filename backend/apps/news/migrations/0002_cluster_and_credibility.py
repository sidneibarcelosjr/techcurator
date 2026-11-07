from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cluster",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("coverage", models.IntegerField(default=1)),
                ("size", models.IntegerField(default=1)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-coverage", "-size"],
            },
        ),
        migrations.AddField(
            model_name="article",
            name="cluster",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="articles",
                to="news.cluster",
            ),
        ),
        migrations.AddField(
            model_name="article",
            name="credibility_score",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="article",
            name="credibility_label",
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
