from decimal import Decimal

from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import StructBlock, URLBlock, RichTextBlock, ListBlock
from wagtail.admin.panels import FieldPanel
from wagtail import blocks
from wagtail.images import get_image_model
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.shortcuts import render, redirect
from decimal import Decimal, InvalidOperation

class PageAccueil(Page):
    template = "pages/accueil.html"
    texte_intro = RichTextField(blank=True, verbose_name="Texte d'introduction")
    content_panels = Page.content_panels + [FieldPanel('texte_intro')]

# ----- Réalisation -----
class RealisationBlock(blocks.StructBlock):
    texte = blocks.RichTextBlock(required=False)
    video = blocks.URLBlock(required=False)
    galerie = blocks.ListBlock(ImageChooserBlock(), required=False)

    class Meta:
        icon = "doc-full-inverse"
        label = "Bloc Réalisation"


class RealisationPage(Page):
    template = "pages/realisation.html"
    description = RichTextField(blank=True)
    contenu = StreamField([("bloc", RealisationBlock())], blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("contenu"),   # ✅ plus besoin de StreamFieldPanel
    ]


# ----- Catalogue -----
class CatalogueItemBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=False)
    titre = blocks.CharBlock(required=True)
    details = blocks.RichTextBlock(required=False)
    prix = blocks.DecimalBlock(required=False, decimal_places=2, max_digits=10, help_text="Prix (optionnel)")

    class Meta:
        icon = "folder-open-inverse"
        label = "Élément de catalogue"

class CataloguePage(Page):
    description = RichTextField(blank=True)
    contenu = StreamField([("item", CatalogueItemBlock())], blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        FieldPanel("contenu"),
    ]

    def serve(self, request):
        # Récupération des items (StreamField)
        items = [block for block in self.contenu if block.block_type == "item"]

        q = (request.GET.get("q") or "").strip().lower()
        pmin = request.GET.get("min")
        pmax = request.GET.get("max")

        def ok_price(value):
            # Si aucun filtre de prix demandé, tout passe
            if not pmin and not pmax:
                return True
            # Pas de prix sur l’item → on l’exclut si un filtre de prix est présent
            if value in (None, ""):
                return False
            try:
                v = Decimal(str(value))
            except (InvalidOperation, ValueError):
                return False
            good = True
            if pmin:
                try:
                    good = good and (v >= Decimal(pmin))
                except (InvalidOperation, ValueError, TypeError):
                    pass
            if pmax:
                try:
                    good = good and (v <= Decimal(pmax))
                except (InvalidOperation, ValueError, TypeError):
                    pass
            return good

        filtered = []
        for b in items:
            data = b.value
            titre = (data.get("titre") or "").lower()
            prix_val = data.get("prix")
            if q and q not in titre:
                continue
            if not ok_price(prix_val):
                continue
            filtered.append(b)

        ctx = {
            "page": self,
            "items": filtered if (q or pmin or pmax) else items,
            "q": request.GET.get("q", ""),
            "min": pmin or "",
            "max": pmax or "",
        }
        return render(request, "pages/catalogue.html", ctx)


class DevisForm(forms.Form):
    nom = forms.CharField(label="Votre nom", max_length=100)
    email = forms.EmailField(label="Email")
    telephone = forms.CharField(label="Téléphone", required=False)
    message = forms.CharField(label="Description", widget=forms.Textarea, required=False)

    # champs cachés (pré-remplis depuis le catalogue/réalisation)
    source_title = forms.CharField(widget=forms.HiddenInput(), required=False)
    source_page = forms.URLField(widget=forms.HiddenInput(), required=False)
    source_image_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)


class DevisPage(Page):
    template = "pages/devis.html"
    intro = RichTextField(blank=True, help_text="Texte d’introduction au-dessus du formulaire")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def serve(self, request):
        # Pré-remplir depuis les paramètres d'URL ?title=...&page=...&image=ID
        initial = {}
        q = request.GET
        if q.get("title"):
            initial["source_title"] = q.get("title")
        if q.get("page"):
            initial["source_page"] = q.get("page")
        if q.get("image"):
            try:
                initial["source_image_id"] = int(q.get("image"))
            except (TypeError, ValueError):
                pass

        if request.method == "POST":
            form = DevisForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                subject = f"Demande de devis : {data.get('nom')}"
                lines = [
                    f"Nom : {data.get('nom')}",
                    f"Email : {data.get('email')}",
                    f"Téléphone : {data.get('telephone')}",
                    f"Message : {data.get('message')}",
                    f"Source titre : {data.get('source_title')}",
                    f"Source page : {data.get('source_page')}",
                    f"Source image id : {data.get('source_image_id')}",
                ]
                body = "\n".join(lines)
                recipient = getattr(settings, "DEFAULT_FROM_EMAIL", "admin@example.com")
                send_mail(subject, body, recipient, [recipient])
                messages.success(request, "Votre demande a été envoyée.")
                return redirect(self.url)
        else:
            form = DevisForm(initial=initial)

        # Charger l'image pour l'aperçu si on a un ID
        Image = get_image_model()
        image_obj = None
        image_id = initial.get("source_image_id") or request.GET.get("image")
        if image_id:
            try:
                image_obj = Image.objects.filter(id=int(image_id)).first()
            except Exception:
                image_obj = None

        ctx = {"page": self, "form": form, "source_image": image_obj}
        return render(request, self.template, ctx)

class ContactPage(Page):
    template = "pages/contact.html"  # <- chemin du template

    intro = RichTextField(blank=True, help_text="Texte d’intro au-dessus des infos.")
    adresse = RichTextField(blank=True, help_text="Adresse postale (peut contenir <br>).")
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    # Requête pour Google Maps (ex: 'Atelier Dupont, Saguenay' ou latitude,longitude)
    map_query = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ex: 'Atelier Dupont Saguenay' ou '48.416, -71.065'"
    )
    map_zoom = models.PositiveIntegerField(default=14, help_text="Niveau de zoom 1–20")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("adresse"),
        FieldPanel("telephone"),
        FieldPanel("email"),
        FieldPanel("map_query"),
        FieldPanel("map_zoom"),
    ]
