% y is sound data, Fs is sample frequency.
%function djezak(title)
% clear
% a=0;
% while (a==0)
%     a = exist('ard','var');
%     ard = arduino('COM12', 'uno');
%     
%     
% end
%
%name = title;
%[y, Fs] = audioread('blame.mp3');
%[y, Fs] = audioread('change.mp3');
%  [y, Fs] = audioread('ghost.mp3');
% [y, Fs] = audioread('run.mp3');
% [y, Fs] = audioread('planes.mp3');
% [y, Fs] = audioread('djpat.mp3');
% [y, Fs] = audioread('roses.mp3');
% [y, Fs] = audioread('Snake-chano .mp3');
%  [y, Fs] = audioread('showmelove.mp3');
%   [y, Fs] = audioread('16TooGood.m4a');
% [y, Fs] = audioread('roseszax.mp3');
% [y, Fs] = audioread('14ChildsPlay.m4a');
  [y, Fs] = audioread('gw.mp3');
%  [y, Fs] = audioread('fkj.mp3');
%  [y, Fs] = audioread('wet.mp3');
% [y, Fs] = audioread('relfections.mp3');
%    [y, Fs] = audioread('handsp2.mp3');
%  [y, Fs] = audioread('likeimgonnaloseyou.mp3');
counter = 1;
window = .02;

lowvals = [];
midvals = [];
highvals = [];
bluepin = 'D3';
redpin = 'D5';
greenpin = 'D9';

while y(counter) == 0
    counter = counter + 1;
end
songstart = counter;
orig = y;
songlength = length(y);
trigger = 0;
maxpower = 0;

while trigger == 0;
    y = orig(counter:counter+window*Fs);
    y = y';
    %t = (1:length(y))/Fs;
    
    N = length(y);
    c = fft(y(1:N))/N;
    p = 2*abs( c(2:floor(N/2)));
    f = (1:floor(N/2)-1)*Fs/N;
    totalpower = sum(p(1:length(f)));
    
    if totalpower>maxpower
        maxpower = totalpower;
    end
    
    counter = counter+window*Fs+1;
    if counter > songlength
        trigger = 1;
    end
end

trigger = 0;
counter = songstart;
while trigger == 0
    y = orig(counter:counter+window*Fs);
    
    y = y';
    %t = (1:length(y))/Fs;
    %t = t';
    
    N = length(y);
    %N = 1024;
    %yfft = fftshift(fft(y,N));
    c = fft(y(1:N))/N;            % compute fft of sound data
    p = 2*abs( c(2:floor(N/2)));         % compute power at each frequency
    f = (1:floor(N/2)-1)*Fs/N;           % frequency corresponding to p
    totalpower = sum(p(1:length(f)));
    
    lowp = sum(p(1:13));
    midp = sum(p(14:30));
    highp = sum(p(31:length(f)));
    
    red = floor((lowp*totalpower/maxpower)*255);
    green = floor((midp*totalpower/maxpower)*255);
    blue = floor((highp*totalpower/maxpower)*255);
    
    lowvals = cat(2, lowvals,red);
    midvals = cat(2, midvals,green);
    highvals = cat(2, highvals, blue);
    counter = counter+window*Fs+1;
    if counter > songlength
        trigger = 1;
        %trigger = trigger + 1;
    end
end
%n = length(y)-1;
%  f=0:Fs/N:Fs-1;
%  wavefft=abs(yfft);
%  figure(1)
%  plot(f,wavefft);
%  xlabel('Freq in Hz');
%  ylabel('Magnitude');
%  title('yeah');

%subplot(1,2,2)
%semilogy(f,p)
%axis([0 8000 10^-4 1])
%title(['Power Spectrum of love.mp3'])

lowvals = lowvals.*(255/max(lowvals));
midvals = midvals.*(255/max(midvals));
highvals = highvals.*(255/max(highvals));

for i = 1:length(lowvals)
    if lowvals(i) > 245
        highvals(i) = 0;
        midvals(i) = 0;
    elseif highvals(i) > 245
        lowvals(i) = 0;
        midvals(i) = 0;
    elseif midvals(i) > 245
        lowvals(i) = 0;
        highvals(i) = 0;
    end
    
    if lowvals(i) > 240
        lowvals(i) = 255;
        %     elseif lowvals(i) < 10
        %         lowvals(i) = 0;
    end
    
    if midvals(i) > 240
        midvals(i) = 255;
        %     elseif midvals(i) < 10
        %         midvals(i) = 0;
    end
    
    if highvals(i) > 240
        highvals(i) = 255;
        %     elseif highvals(i) < 10
        %         highvals(i) = 0;
    end
end

player = audioplayer(orig, Fs);
play(player);
old = 0;
while strcmp(player.Running,'on') == 1
    this = player.CurrentSample;
    
    if (this-songstart)>0 && int32((this-songstart)/Fs/window)>0 && int32((this-songstart)/Fs/window)<=length(lowvals)
        writePWMDutyCycle(ard, redpin, lowvals(int32((this-songstart)/Fs/window))/255);
        writePWMDutyCycle(ard, greenpin, midvals(int32((this-songstart)/Fs/window))/255);
        writePWMDutyCycle(ard, bluepin, highvals(int32((this-songstart)/Fs/window))/255);
    end
    
    interval = this-old;
    if this+interval > length(orig)
        break
    end
    
    old = this;
end

writePWMDutyCycle(ard, bluepin, 0);
writePWMDutyCycle(ard, redpin, 0);
writePWMDutyCycle(ard, greenpin, 0);


%djezak('blame.mp3');






