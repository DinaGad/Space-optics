function zemax_mtf_plot(datafile, outfile)
%ZEMAX_MTF_PLOT  Reproduce an Ansys Zemax OpticStudio polychromatic
%                diffraction MTF plot in MATLAB.
%
%   ZEMAX_MTF_PLOT()
%       Renders using digitised placeholder data (see LOCALDIGITISEDDATA).
%       Use this only to check the styling - the curves are approximate.
%
%   ZEMAX_MTF_PLOT(DATAFILE)
%       Renders the real MTF data exported from OpticStudio as text.
%       In OpticStudio:  open the FFT MTF / Huygens MTF analysis window,
%       then  Text  tab  ->  File  ->  Save As  ->  *.txt
%       (or right-click the plot -> Export -> Text).
%
%   ZEMAX_MTF_PLOT(DATAFILE, OUTFILE)
%       Also writes the figure to OUTFILE (.pdf, .png, .eps, .tif).
%
%   Example
%       zemax_mtf_plot('Optics_Zemax_MTF.txt', 'fig_mtf.pdf')
%
%   Reproduces: Optics_Zemax.ZMX, Configuration 4 of 4,
%               0.4880-0.8500 um, Surface: Image (CMOS)

% ─────────────────────────────────────────────────────────────
% Header metadata - edit to match your own analysis
% ─────────────────────────────────────────────────────────────
META.title      = 'Polychromatic Diffraction MTF';
META.date       = '13/09/2026';
META.waveband   = 'Data for 0.4880 to 0.8500 \mum.';
META.surface    = 'Surface: Image (CMOS)';
META.legendNote = 'Legend items refer to Field positions';
META.vendor     = 'Zemax';
META.version    = 'Ansys Zemax OpticStudio 2025 R1.00';
META.filename   = 'Optics_Zemax.ZMX';
META.config     = 'Configuration 4 of 4';

FREQ_MAX = 90;          % cycles per mm
FIELDS   = [0.0000, 0.7778, 1.1000];     % degrees

% Zemax uses fully saturated RGB, one hue per field position
COLORS = [0 0 1;         % field 1 - blue
          0 1 0;         % field 2 - green
          1 0 0];        % field 3 - red

% ─────────────────────────────────────────────────────────────
% Load data
% ─────────────────────────────────────────────────────────────
if nargin < 1 || isempty(datafile)
    [f, M] = localDigitisedData();
    warning('zemax:placeholder', ...
        ['Using digitised placeholder curves. These were traced from a ' ...
         'raster image and are NOT your optical prescription. Export ' ...
         'the MTF text file from OpticStudio and pass it as an argument.']);
else
    [f, M] = readZemaxMTF(datafile);
end

nCurves = size(M, 2);
if nCurves ~= 2 * numel(FIELDS)
    warning('zemax:curveCount', ...
        'Found %d data columns but %d field positions are configured.', ...
        nCurves, numel(FIELDS));
end

% Build legend entries: Zemax orders them T,S per field
labels = cell(1, nCurves);
styles = cell(1, nCurves);
cols   = zeros(nCurves, 3);
for k = 1:nCurves
    fi = ceil(k / 2);                          % field index
    isTangential = mod(k, 2) == 1;
    fi = min(fi, numel(FIELDS));
    labels{k} = sprintf('%.4f (deg)-%s', FIELDS(fi), ...
                        ternary(isTangential, 'Tangential', 'Sagittal'));
    styles{k} = ternary(isTangential, '-', ':');
    cols(k,:) = COLORS(min(fi, size(COLORS,1)), :);
end

FONT = pickMonoFont();

% ─────────────────────────────────────────────────────────────
% Figure
% ─────────────────────────────────────────────────────────────
fig = figure('Color', 'w', 'Units', 'pixels', ...
             'Position', [100 100 600 550], ...
             'Name', META.title, 'NumberTitle', 'off', ...
             'PaperPositionMode', 'auto');

% ── Main MTF axes ────────────────────────────────────────────
ax = axes('Parent', fig, 'Units', 'normalized', ...
          'Position', [0.095 0.435 0.800 0.525]);
hold(ax, 'on');

h = gobjects(1, nCurves);
for k = 1:nCurves
    h(k) = plot(ax, f, M(:,k), styles{k}, ...
                'Color', cols(k,:), 'LineWidth', 1);
end

set(ax, 'XLim', [0 FREQ_MAX], 'YLim', [0 1], ...
        'XTick', 0:10:FREQ_MAX, 'YTick', 0:0.2:1, ...
        'FontName', FONT, 'FontSize', 11, ...
        'LineWidth', 0.50, ...
         'Box', 'on', ...
        'Layer', 'top');

ax.XLabel.Interpreter = 'latex';
ax.YLabel.Interpreter = 'latex';

% Zemax labels the origin as bare "0" and the rest with one decimal
xl = arrayfun(@(v) sprintf('%.1f', v), 0:10:FREQ_MAX, 'UniformOutput', false);
xl{1} = '0';
yl = arrayfun(@(v) sprintf('%.1f', v), 0:0.2:1, 'UniformOutput', false);
yl{1} = '0';
set(ax, 'XTickLabel', xl, 'YTickLabel', yl);
ax.XLabel.Interpreter = 'latex';
ax.YLabel.Interpreter = 'latex';

grid(ax, 'on');
%set(ax, 'GridColor', [0.72 0.72 0.72], 'GridAlpha', 1.0, ...
%        'GridLineStyle', '-');

% Light grey closing border on top and right (Zemax draws the left and
% bottom spines heavy black, the other two as thin grid-coloured lines)
line(ax, [0 FREQ_MAX], [1 1], 'Color', [0.72 0.72 0.72], ...
     'LineWidth', 0.6, 'HandleVisibility', 'off');
line(ax, [FREQ_MAX FREQ_MAX], [0 1], 'Color', [0.72 0.72 0.72], ...
     'LineWidth', 0.6, 'HandleVisibility', 'off');

xlabel(ax, 'Spatial Frequency in cycles per mm', ...
       'FontName', FONT, 'FontSize', 13);
ylabel(ax, 'Modulus Transfer Function', ...
       'FontName', FONT, 'FontSize', 13);
ax.XLabel.Interpreter = 'latex';
ax.YLabel.Interpreter = 'latex';

% ── Legend panel ─────────────────────────────────────────────
axL = axes('Parent', fig, 'Units', 'normalized', ...
           'Position', [0.155 0.255 0.590 0.080], ...
           'XLim', [0 1], 'YLim', [0 1], 'Visible', 'on');
hold(axL, 'on');

% Enclosing box
%rectangle('Parent', axL, 'Position', [0 0 1 1], ...
%          'EdgeColor', 'k', 'LineWidth', 0.8);

colX  = [0.015 0.345 0.670];       % three columns
rowY  = [0.70 0.28];               % two rows
for k = 1:nCurves
    c = mod(k-1, 3) + 1;
    r = floor((k-1) / 3) + 1;
    if r > numel(rowY), break; end
    x0 = colX(c);  y0 = rowY(r);

    drawCheckbox(axL, x0, y0);

    % Line sample
    line(axL, [x0+0.030 x0+0.075], [y0 y0], ...
         'Color', cols(k,:), 'LineStyle', styles{k}, 'LineWidth', 1.4);

    text(axL, x0+0.082, y0, labels{k}, ...
         'FontName', FONT, 'FontSize', 10, ...
         'VerticalAlignment', 'middle', 'Interpreter', 'none');
end

% ── Footer information panel ─────────────────────────────────
axF = axes('Parent', fig, 'Units', 'normalized', ...
           'Position', [0.000 0.020 1.000 0.190], ...
           'XLim', [0 1], 'YLim', [0 1], 'Visible', 'off');
hold(axF, 'on');

xL = 0.005; xR = 0.995; xSplit = 0.605;
line(axF, [xL xR], [1 1],       'Color','k','LineWidth',0.8);   % top rule
line(axF, [xL xR], [0.78 0.78], 'Color','k','LineWidth',0.8);   % title rule
line(axF, [xL xR], [0 0],       'Color','k','LineWidth',0.8);   % bottom rule
line(axF, [xL xL], [0 1],       'Color','k','LineWidth',0.8);
line(axF, [xR xR], [0 1],       'Color','k','LineWidth',0.8);
line(axF, [xSplit xSplit], [0 0.78], 'Color','k','LineWidth',0.8);
line(axF, [xSplit xR], [0.39 0.39],  'Color','k','LineWidth',0.8);

text(axF, (xL+xR)/2, 0.89, META.title, ...
     'FontName', FONT, 'FontSize', 13, ...
     'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');

leftLines = {META.date, META.waveband, META.surface, '', META.legendNote};
yTop = 0.68;
for k = 1:numel(leftLines)
    text(axF, xL+0.012, yTop - (k-1)*0.145, leftLines{k}, ...
         'FontName', FONT, 'FontSize', 10, ...
         'VerticalAlignment', 'middle');
end

xMidR = (xSplit + xR) / 2;
text(axF, xMidR, 0.67, META.vendor, 'FontName', FONT, 'FontSize', 10, ...
     'HorizontalAlignment','center','VerticalAlignment','middle');
text(axF, xMidR, 0.51, META.version, 'FontName', FONT, 'FontSize', 10, ...
     'HorizontalAlignment','center','VerticalAlignment','middle');
text(axF, xMidR, 0.26, META.filename, 'FontName', FONT, 'FontSize', 10, ...
     'HorizontalAlignment','center','VerticalAlignment','middle','Interpreter','none');
text(axF, xMidR, 0.11, META.config, 'FontName', FONT, 'FontSize', 10, ...
     'HorizontalAlignment','center','VerticalAlignment','middle');

% ── Export ───────────────────────────────────────────────────
if nargin >= 2 && ~isempty(outfile)
    try
        exportgraphics(fig, outfile, 'Resolution', 1000, ...
                       'BackgroundColor', 'white');
    catch
        % Pre-R2020a fallback: pick the driver from the file extension
        [~, ~, ext] = fileparts(outfile);
        switch lower(ext)
            case '.png',            drv = '-dpng';
            case {'.tif', '.tiff'}, drv = '-dtiff';
            case '.eps',            drv = '-depsc2';
            case '.svg',            drv = '-dsvg';
            otherwise,              drv = '-dpdf';
        end
        print(fig, outfile, drv, '-r600');
    end
    fprintf('Figure written to %s\n', outfile);
end

% ── Console summary ──────────────────────────────────────────
fprintf('\nMTF at Nyquist-relevant frequencies:\n');
for fq = [20 50 100]
    if fq > max(f), continue; end
    vals = interp1(f, M, fq);
    fprintf('  %5.1f cyc/mm : min %.3f  max %.3f  mean %.3f\n', ...
            fq, min(vals), max(vals), mean(vals));
end

end % ===================== main =====================


% ─────────────────────────────────────────────────────────────
function drawCheckbox(ax, x, y)
%DRAWCHECKBOX  Small ticked box mimicking the Zemax legend toggle.
w = 0.016;  hgt = 0.30;
rectangle('Parent', ax, 'Position', [x-w/2, y-hgt/2, w, hgt], ...
          'EdgeColor', 'k', 'FaceColor', 'w', 'LineWidth', 0.6);
line(ax, [x-w*0.28, x-w*0.05, x+w*0.30], ...
         [y+hgt*0.02, y-hgt*0.22, y+hgt*0.24], ...
     'Color', [0 0.55 0], 'LineWidth', 1.1);
end


% ─────────────────────────────────────────────────────────────
function [f, M] = readZemaxMTF(file)
%READZEMAXMTF  Parse an OpticStudio MTF text export.
%
%   Tolerant of the header block, blank lines and UTF-16 encoding that
%   OpticStudio writes. Takes the first column as spatial frequency and
%   every remaining numeric column as an MTF curve.

if exist(file, 'file') ~= 2
    error('zemax:fileNotFound', 'File not found: %s', file);
end

% OpticStudio commonly writes UTF-16LE; try that, then fall back
txt = '';
encodings = {'UTF-16LE', 'UTF-8', ''};
for e = 1:numel(encodings)
    try
        if isempty(encodings{e})
            fid = fopen(file, 'r');
        else
            fid = fopen(file, 'r', 'n', encodings{e});
        end
        if fid < 0, continue; end
        raw = fread(fid, '*char')';
        fclose(fid);
        if numel(strfind(raw, char(10))) > 3
            txt = raw; break;
        end
    catch
        if exist('fid','var') && fid > 0, fclose(fid); end
    end
end
if isempty(txt)
    error('zemax:unreadable', 'Could not read %s in any known encoding.', file);
end

lines = regexp(txt, '\r\n|\n|\r', 'split');

rows = [];
for k = 1:numel(lines)
    s = strtrim(lines{k});
    if isempty(s), continue; end
    tok = regexp(s, '[\s,\t]+', 'split');
    v = str2double(tok);
    if numel(v) >= 3 && all(isfinite(v))
        if isempty(rows)
            rows = v(:)';
        elseif numel(v) == size(rows, 2)
            rows(end+1, :) = v(:)';  %#ok<AGROW>
        end
    end
end

if isempty(rows)
    error('zemax:noData', ...
        ['No numeric data block found in %s. Make sure you exported the ' ...
         'TEXT tab of the MTF window, not a screenshot.'], file);
end

f = rows(:, 1);
M = rows(:, 2:end);

% Guard against a stray column of zeros or out-of-range values
keep = all(M >= -1e-6 & M <= 1 + 1e-6, 1);
M = M(:, keep);

fprintf('Read %s: %d frequency points, %d MTF curves\n', ...
        file, numel(f), size(M, 2));
end


% ─────────────────────────────────────────────────────────────
function [f, M] = localDigitisedData()
%LOCALDIGITISEDDATA  Curves traced from the reference raster image.
%
%   APPROXIMATE. Provided so the styling can be checked without a Zemax
%   export. Replace with real data before using any figure in a paper.

f = (0:5:100)';

T0 = [1.000 0.955 0.912 0.870 0.830 0.792 0.755 0.719 0.685 0.654 ...
      0.624 0.595 0.567 0.541 0.516 0.493 0.472 0.453 0.437 0.425 0.418]';
S0 = [1.000 0.958 0.918 0.878 0.840 0.803 0.768 0.734 0.702 0.672 ...
      0.643 0.616 0.590 0.565 0.542 0.520 0.500 0.483 0.468 0.455 0.446]';
T1 = [1.000 0.945 0.885 0.845 0.795 0.755 0.720 0.690 0.660 0.632 ...
      0.605 0.580 0.556 0.533 0.512 0.493 0.477 0.464 0.454 0.448 0.445]';
S1 = [1.000 0.950 0.898 0.850 0.808 0.768 0.730 0.697 0.665 0.635 ...
      0.607 0.580 0.554 0.530 0.508 0.488 0.470 0.455 0.443 0.436 0.433]';
T2 = [1.000 0.958 0.918 0.878 0.838 0.798 0.760 0.722 0.686 0.651 ...
      0.618 0.586 0.556 0.528 0.501 0.477 0.455 0.435 0.419 0.406 0.398]';
S2 = [1.000 0.962 0.925 0.888 0.852 0.818 0.785 0.753 0.722 0.693 ...
      0.666 0.640 0.616 0.594 0.573 0.554 0.537 0.523 0.516 0.512 0.510]';

M = [T0 S0 T1 S1 T2 S2];
end


% ─────────────────────────────────────────────────────────────
function fn = pickMonoFont()
%PICKMONOFONT  First available monospace face, matching Zemax's look.
cands = {'Courier New', 'Consolas', 'DejaVu Sans Mono', ...
         'Liberation Mono', 'Menlo', 'Monospaced', 'Courier'};
try
    avail = listfonts;
    for k = 1:numel(cands)
        if any(strcmpi(avail, cands{k}))
            fn = cands{k};
            return
        end
    end
catch
    % listfonts unavailable in some headless configurations
end
fn = 'FixedWidth';
end


% ─────────────────────────────────────────────────────────────
function out = ternary(cond, a, b)
if cond, out = a; else, out = b; end
end
