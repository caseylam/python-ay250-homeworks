from flask import Flask
import io
import random
from flask import Flask, Response, flash, request, redirect, url_for, send_from_directory, render_template
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)

# alert_id=1
# @app.route('/plot<alert_id>.png')
# def plot_png(time, mag, title=alert_id):
#     fig = create_figure(time, mag)
#     output = io.BytesIO()
#     FigureCanvas(fig).print_png(output)
#     return Response(output.getvalue(), mimetype='image/png')

# def create_figure(time, mag, mag_err=None, title=None):
#     fig = Figure()
#     axis = fig.add_subplot(1, 1, 1)
#     axis.invert_yaxis()
#     if mag_err is not None:
#         axis.errorbar(time, mag, yerr=mag_err, ls='none', marker='.')
#     else:
#         axis.plot(time, mag)
        
#     if title is not None:
#         axis.set_title(title)
#     return fig

@app.route('/print<int:ii>')
def print_num(ii):
    return render_template('test_number.html', 
                           next_page=url_for('print_num', ii=ii+1), 
                           prev_page=url_for('print_num', ii=ii-1), 
                           home=url_for('home'),
                           ii=ii, qmax=10)

@app.route('/')
def home():
    ii=1
    return render_template('test_display.html', 
                           next_page=url_for('print_num', ii=ii+1), 
                           prev_page=url_for('print_num', ii=ii-1), 
                           ii=ii, qmax=10,
                          num_list=range(10))


if __name__ == '__main__':
    app.run(port=8001, debug = True)
