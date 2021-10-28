from urllib.parse import urlparse, urlunparse
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import FieldError


def object_relation_base_factory(prefix=None, prefix_verbose=None, add_related_name=False, 
                                limit_content_type_choices_to=None, is_required=False):
    """
    Retorna uma classe mixin para chaves estrangeiras genéricas usando "Content type - ID do objeto" com nomes de 
    campos dinâmicos. Esta função é apenas um gerador de classe.

    Parameters:
    prefix:             um prefixo, que é adicionado na frente dos campos
    prefix_verbose:     um verbose name do prefixo, usado para gera um título para a coluna do campo do objeto de conteúdo 
                        no Admin
    add_related_name:   um valor booleano indicando que um nome relacionado para o conteúdo gerado tipo de foreign key 
                        deve ser adicionado. Esse valor deve ser verdadeiro, se você usar mais de um ObjectRelationBase 
                        em seu modelo.
    Os campos do modelo sao criados usando este esquema de nome:
        <<prefix>>_content_type
        <<prefix>>_object_id
        <<prefix>>_content_object
    """

    p = ""
    if prefix:
        p = f"{prefix}_"
        prefix_verbose = prefix_verbose or _("Related object")
        limit_content_type_choices_to = limit_content_type_choices_to or {}
        content_type_field = f"{p}content_type"
        object_id_field = f"{p}object_id"
        content_object_field = f"{p}content_object"

    class TheClass(models.Model):
        class Meta:
            abstract = True

        if add_related_name:
            if not prefix:
                raise FieldError("if add_related_name is set to True, a prefix must be given")
            related_name = prefix
        else:
            related_name = None

        optional = not is_required
        ct_verbose_name = _(f"{prefix_verbose}'s type (model)")
        content_type = models.ForeignKey(ContentType, verbose_name=ct_verbose_name, related_name=related_name,
                                        blank=optional, null=optional, 
                                        help_text="Por favor selecione o tipo  (model) para a relação que você quer fazer",
                                        limit_choices_to=limit_content_type_choices_to, on_delete=models.CASCADE)
        fk_verbose_name = prefix_verbose
        object_id = models.CharField(fk_verbose_name, blank=optional, null=False, 
                                    help_text="Por favor, digite o ID do objeto relacionado", max_length=255,
                                    default="")
        content_object = GenericForeignKey(ct_field=content_type_field, fk_field=object_id_field)
        TheClass.add_to_class(content_type_field, content_type)
        TheClass.add_to_class(object_id_field, object_id)
        TheClass.add_to_class(content_object_field, content_object)

        return TheClass
        

class MetaTagsBase(models.Model):
    """
    Classe abstrata para gerar meta tags
    """

    meta_keywords = models.CharField(_("Keywords"), max_length=255, blank=True, help_text=
                                        _("Separa as palavras-chave com vírgulas"))
    meta_description = models.CharField(_("Description"), max_length=255, blank=True)
    meta_author = models.CharField(_("Author"), max_length=255, blank=True)
    meta_copyright = models.CharField(_("Copyright"), max_length=255, blank=True)

    class Meta:
        abstract = True

    def get_meta_field(self, name, content):
        tag = ""
        if name and content:
            tag = render_to_string("core/includes/meta_field.html",
            {
                "name": name,
                "content": content,
            })
        
        return mark_safe(tag)

    def get_meta_keywords(self):
        return self.get_meta_field("keywords", self.meta_keywords)

    def get_meta_description(self):
        return self.get_meta_field("description", self.meta_description)

    def get_meta_author(self):
        return self.get_meta_field("author", self.meta_author)

    def get_meta_copyright(self):
        return self.get_meta_field("copyright", self.meta_copyright)

    def get_meta_tafs(self):
        return mark_safe("\n".join((
            self.get_meta_keywords(),
            self.get_meta_description(),
            self.meta_author(),
            self.get_meta_copyright(),
        )))


class UrlBase(models.Model):
    """
    Substituiçao para o get_absolute_url()
    Modelos que estendem este mixin devem ter get_url ou get_url_path implementado.
    Args:
        models ([type]): [description]
    """

    class Meta:
        abstract = True

    def get_url(self):
        if hasattr(self.get_url_path, "dont_recurse"):
            raise NotImplementedError
        
        try:
            path = self.get_url_path()
        except NotImplementedError:
            raise

        return settings.WEBSITE_URL + path

    get_url.dont_recurse = True

    def get_url_path(self):
        if hasattr(self.get_url, "dont_recurse"):
            raise NotImplementedError
        
        try:
            url = self.get_url()
        except NotImplementedError:
            raise
        
        bits = urlparse(url)
        return urlunparse(("", "") + bits[2:])

    get_url_path.dont_recurse = True
    
    def get_absolute_url(self):
        return self.get_url()


class CreationModificationDateBase(models.Model):
    """
    Classe Base abstrata com criacao e modificacao de data e hora
    Args:
        models ([type]): [description]
    """

    created = models.DateTimeField(_("Creation date and time"), auto_now_add=True)
    modified = models.DateTimeField(_("Modification date and time"), auto_now=True)

    class Meta:
        abstract = True
