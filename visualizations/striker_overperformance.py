from matplotlib.figure import Figure

from PIL import Image
from urllib.request import urlopen
import numpy as np
from matplotlib import pyplot as plt
plt.style.use('dark_background')

def add_image(image, fig, left, bottom, width=None, height=None, **kwargs):
    """ Adds an image to a figure using fig.add_axes and ax.imshow

    If downsampling an image 'hamming' interpolation is recommended

    Parameters
    ----------
    image: array-like or PIL image
        The image data.
    fig: matplotlib.figure.Figure
        The figure on which to add the image.
    left, bottom: float
        The dimensions left, bottom of the new axes.
        All quantities are in fractions of figure width and height.
        This positions the image axis in the figure left% in from the figure side
        and bottom% in from the figure bottom.
    width, height: float, default None
        The width, height of the new axes.
        All quantities are in fractions of figure width and height.
        For best results use only one of these so the image is scaled appropriately.
    **kwargs : All other keyword arguments are passed on to matplotlib.axes.Axes.imshow.

    Returns
    -------
    matplotlib.axes.Axes

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from PIL import Image
    >>> from mplsoccer import add_image
    >>> from urllib.request import urlopen
    >>> fig, ax = plt.subplots()
    >>> image_url = 'https://upload.wikimedia.org/wikipedia/commons/b/b8/Messi_vs_Nigeria_2018.jpg'
    >>> image = urlopen(image_url)
    >>> image = Image.open(image)
    >>> ax_image = add_image(image, fig, left=0.1, bottom=0.2, width=0.4, height=0.4)
    """
    if isinstance(image, Image.Image):
        image_width, image_height = image.size
    else:
        image_height, image_width = image.shape[:2]

    image_aspect = image_width / image_height

    figsize = fig.get_size_inches()
    fig_aspect = figsize[0] / figsize[1]

    if height is None:
        height = width / image_aspect * fig_aspect

    if width is None:
        width = height * image_aspect / fig_aspect

    # add image
    ax_image = fig.add_axes((left, bottom, width, height))
    ax_image.axis('off')  # axis off so no labels/ ticks

    ax_image.imshow(image, **kwargs)

    return ax_image



def plot_finishing_performance(full_df, this_season_df, league):
  fig=Figure(figsize=(10,8))
  layout="""
  t
  B
  f
  """
  axes = fig.subplot_mosaic(layout, gridspec_kw={
          # set the height ratios between the rows
          "height_ratios": [0.6, 6, 0.6],
        
      },)
  season = this_season_df['season'].tolist()[0]
  for a in ['t','f']:
    axes[a].axis('off')
  ax = axes['B']
  ax.axhline(y=0, color='grey')
  ax.plot(full_df['shots_total_cumulative'], full_df['npxg_plus_per_shot_cumulative'],zorder=2, label='Cumulative NPxG+/Shot Since 2017')
  ax.plot(this_season_df['display_shots_total'], this_season_df['npxg_plus_per_shot_cumulative'],zorder=2, color='purple', label=f'Cumulative NPxG+/Shot in {season}-{season+1} Season')
  for m in [-2, -1, 1, 2]:
    ax.plot(full_df['shots_total_cumulative'], full_df[f'conf{m}'], linestyle='--', color='orange', alpha = 0.75/np.abs(m),zorder=2)
  ax.set_xlabel('Total Shots Taken (since 2017)', fontdict={'size':12})
  ax.set_ylabel('NPxG+ (with 67% and 95% confidence intervals)', fontdict={'size':12})
  #ax.set_title(f"{_name.title()} NPxG+ in 2021 compared to historical trend", fontdict={'size':18})
  ax.legend()
  ax.grid(alpha=0.05, linestyle='--')

  axes["f"].text(
        0.08,
        0.5,
        f"@McLachBot\nhttps://www.mclachbot.com/striker_performance/{league}",
        color="#c7d5cc",
        va="center",
        ha="left",
        fontsize=12,
     #   fontproperties=robotto_regular.prop,
    )
  image = Image.open(
        urlopen(
            "https://pbs.twimg.com/profile_images/1490059544734703620/7avjgS-D_400x400.jpg"
        )
    )
  player_name = full_df['player'].tolist()[0].title()
  team = ', '.join(this_season_df['squad'].apply(lambda x: x.replace('_',' ').title()).unique())
  actual_league = ', '.join(this_season_df['comp'].apply(lambda x: x.replace('_',' ').title()).unique())
  
  add_image(image, fig, left=0.10, bottom=0.10, width=0.07, height=0.07)
  axes["t"].text(
        0.5,
        0.7,
        f"{player_name.title()}. {team}, {actual_league}.\n NPxG+ in {season} compared to historical trend",
        color="#c7d5cc",
        va="center",
        ha="center",
        fontsize=18,
    )
  
  return fig