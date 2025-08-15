# ¿Qué significa "Fuerza" en el Simulador?

## Explicación Simple (Modo Juego)

En el **Modo Juego** (Opción 4), cuando ves el control de "💪 Fuerza", se refiere a:

**"¿Qué tan fuerte quieres disparar el misil?"**

- **Más Fuerza** = El misil va más rápido y llega más lejos
- **Menos Fuerza** = El misil va más lento y no llega tan lejos

Es como un videojuego donde controlas la potencia del disparo.

## Explicación Técnica (Para Entender la Física)

### ¿Qué es realmente la "Fuerza"?

La "Fuerza" en el simulador representa la **compresión del resorte** que lanza el misil:

1. **Resorte comprimido**: Imagina un resorte que empujas hacia adentro
2. **Energía almacenada**: Mientras más lo comprimes, más energía acumula
3. **Liberación**: Cuando lo sueltas, esa energía se convierte en velocidad del misil

### Fórmula Física

```
Energía del resorte = ½ × k × x²
Energía cinética = ½ × m × v₀²

Por conservación de energía:
v₀ = x × √(k/m)
```

Donde:
- **x** = compresión del resorte (esto es la "Fuerza" en el juego)
- **k** = constante del resorte (rigidez)
- **m** = masa del proyectil
- **v₀** = velocidad inicial del misil

### Valores en el Simulador

Según `baseline.json`:

**Atacante:**
- k = 20,000 N/m (constante del resorte)
- x = 0.50 m (compresión por defecto)
- m = 10.0 kg (masa del proyectil)

**Defensor:**
- k = 25,000 N/m (resorte más rígido)
- x = 0.50 m (compresión por defecto)
- m = 12.0 kg (proyectil más pesado)

### Ejemplo de Cálculo

Con los valores por defecto del atacante:
```
v₀ = 0.50 × √(20000/10)
v₀ = 0.50 × √2000
v₀ = 0.50 × 44.72
v₀ ≈ 22.36 m/s
```

### Rangos en el Simulador

- **Mínimo**: 0.05 m (fuerza muy baja)
- **Máximo**: 1.0 m (fuerza máxima)

Si cambias la "Fuerza" a 1.0:
```
v₀ = 1.0 × √(20000/10) ≈ 44.72 m/s
```

## Analogía del Mundo Real

Piensa en:

1. **Arco y flecha**: Mientras más estires la cuerda (compresión), más fuerte sale la flecha
2. **Tirachinas**: Más estiramiento = más velocidad
3. **Cañón con resorte**: Más compresión = más potencia

## En Resumen

| Control | Significado Físico | Efecto en el Juego |
|---------|-------------------|-------------------|
| "💪 Fuerza" | Compresión del resorte (metros) | Velocidad inicial del misil |
| Más fuerza | Más compresión (hasta 1.0 m) | Misil más rápido y con mayor alcance |
| Menos fuerza | Menos compresión (mínimo 0.05 m) | Misil más lento y menor alcance |

**¡Es física real aplicada de forma divertida!** 🚀
