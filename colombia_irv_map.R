library(tidyverse)
library(dplyr)
library(geojsonio)
library(broom)
library(gridExtra)

spdf <- geojson_read("mpio.json", method = "local", what = "sp")

spdf@data$code <- paste(spdf@data$DPTO, spdf@data$MPIO, sep = "_")

spdf_fortified <- tidy(spdf, region = "code")

data <- read_csv("plebiscito_mpios.csv")
data$code <- paste(data$cod_depto, data$cod_mpio, sep = "_")

spdf_fortified <- spdf_fortified %>%
  left_join(. , data, by = c("id" = "code"))

irv_map <- ggplot() +
  geom_polygon(data = spdf_fortified, aes(fill = IRV, x = long, y = lat, group = group), size = 0, alpha = 0.9) +
  theme_void() +
  scale_fill_viridis_c(option = "magma", begin = 0.6, end = 1, direction = -1, breaks = c(0.15,0.3,0.45,0.6, 0.75, 0.9, 1), name = "Índice de riesgo de victimización", guide = guide_legend(keyheight = unit(3, units = "mm"), keywidth = unit(10, units = "mm"), label.position = "bottom", title.position = "top", nrow = 1)) +
  labs(
    title = "Índice de riesgo de victimización por municipio",
    caption = "Data: IRV              \nAuthor: Santiago Bacaro"
  ) +
  theme(
    text = element_text(color = "#22211d"),
    plot.background = element_rect(fill = "#f5f5f2", color = NA),
    panel.background = element_rect(fill = "transparent", color = NA),
    legend.background = element_rect(fill = "#f5f5f2", color = NA),
    plot.title = element_text(size = 14, hjust = 0.01, color = "#4e4d47", margin = margin(b = -1, t = 0.4, l = 2, unit = "cm")),
    plot.caption = element_text(size = 08, color = "#4e4d47", margin = margin(b = 0.3, r = -99, unit = "cm")),
    legend.position = c(0.35, 0.02)
  ) +
  coord_map()

preferencia <- ggplot() +
  geom_polygon(data = spdf_fortified, aes(fill = Preferencia, x = long, y = lat, group = group), size = 0.1, alpha = 0.9, color = "#f5f5f2") +
  theme_void() +
  scale_fill_manual(values = c("#ef7564", "#fffff8"), na.value = "grey") +
  labs(
    title = "Porcentaje de apoyo al 'No' por municipio",
    caption = "Data: https://registraduria.gov.co\nAuthor: Santiago Bacaro"
  ) +
  theme(
    text = element_text(color = "#22211d"),
    plot.background = element_rect(fill = "#f5f5f2", color = NA),
    panel.background = element_rect(fill = "transparent", color = NA),
    legend.background = element_rect(fill = "#f5f5f2", color = NA),
    plot.title = element_text(size = 14, hjust = 0.01, color = "#4e4d47", margin = margin(b = -1, t = 0.4, l = 2, unit = "cm")),
    plot.caption = element_text(size = 08, color = "#4e4d47", margin = margin(b = 0.3, r = -99, unit = "cm")),
    legend.position = c(0.35, 0.02)
  ) +
  coord_map()

#grid.arrange(irv_map, no_percentage, ncol = 2)
g <- arrangeGrob(irv_map, preferencia, ncol = 2)
ggsave("irv_vs_preferencia.png", g, height = 6.5, width = 10.5)