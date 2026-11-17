(function ($) {
  "use strict";

  $(function () {
    $(".slider-wrap").each(function () {
      var slider = $(this);
      var slideCount = slider.children(".slider-item").length;

      if (!slideCount) return;
      if (slideCount === 1) {
        slider.addClass("canaco-single-news-slider");
        return;
      }

      slider.slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        autoplaySpeed: 5000,
        autoplay: true,
        dots: true,
        arrows: true,
        infinite: true,
      });
    });
  });
})(jQuery);
